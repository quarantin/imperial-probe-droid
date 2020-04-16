#!/usr/bin/env python3

import sys
import json
import asyncio
import libswgoh
import traceback
from datetime import datetime, timedelta

from constants import MINUTE
from swgohhelp import api_swgoh_guilds, SwgohHelpException

import DJANGO
from swgoh.models import PremiumGuild

from crawlerdiffer import CrawlerDiffer

SAFETY_TTL = 10 * MINUTE

DEFAULT_GUILD_EXPIRE = 24
DEFAULT_PLAYER_EXPIRE = 24

class Crawler(asyncio.Future):

	async def update_player(self, guild, ally_code):

		ally_code = str(ally_code)
		profile = await libswgoh.get_player_profile(ally_code=ally_code, session=self.session)
		if not profile:
			self.logger.error('Failed retrieving profile for allycode %s' % ally_code)
			raise Exception('Failed retrieving profile for %s, skipping.' % ally_code)

		# TODO: Fix this atrocity
		profile = json.loads(json.dumps(profile))

		if 'name' not in profile:
			self.logger.warning('Failed retrieving profile for allycode %s' % ally_code)
			return []

		#if 'roster' in profile:
		#	profile['roster'] = { x['defId']: x for x in profile['roster'] }

		player_key = 'player|%s' % ally_code
		new_profile = profile
		old_profile = await self.get_player(ally_code, fetch=False)
		if not old_profile:
			old_profile = new_profile

		messages = self.differ.check_diff(guild, old_profile, new_profile)

		self.cache_player(new_profile)

		if messages:

			formated = []
			for message in messages:
				formated.append(json.dumps(message))

			messages_key = 'messages|%s' % guild.guild_id
			self.redis.rpush(messages_key, *formated)

		self.logger.debug(ally_code)

	async def get_player(self, ally_code, fetch=True):

		key = 'player|%s' % ally_code
		profile = self.redis.get(key)
		if profile:
			return json.loads(profile.decode('utf-8'))

		profile = await libswgoh.get_player_profile(ally_code=ally_code, session=self.session)
		if profile:
			id_key = 'playerid|%s' % profile['id']
			expire = timedelta(hours=DEFAULT_PLAYER_EXPIRE)
			self.redis.setex(key, expire, json.dumps(profile))
			self.redis.setex(id_key, expire, profile['allyCode'])

		return profile

	async def refresh_players(self, selectors, channels, selectors_only=False):

		failed_ac = []
		failed_ch = []

		for selector, channel in zip(selectors, channels):

			guild = await self.get_guild(selector)
			if not guild:
				self.logger.warning('Guild not found in redis: %s' % selector)
				continue

			self.logger.debug('%s (%s)' % (guild['id'], guild['name']))

			premium_guild = PremiumGuild.get_guild(guild['id'])
			if not premium_guild:
				self.logger.warning('Guild not found in redis: %s' % guild['id'])
				continue

			for member in guild['roster']:

				if selectors_only is True and str(member['allyCode']) not in selectors:
					continue

				try:
					await self.update_player(premium_guild, member['allyCode'])

				except Exception as err:
					print(err)
					#print(traceback.format_exc())
					failed_ac.append(str(member['allyCode']))
					failed_ch.append(channel)

		return failed_ac, failed_ch

	def cache_player(self, player):

		player_key = 'player|%s' % player['allyCode']
		player_key_id = 'playerid|%s' % player['id']
		player_expire = timedelta(hours=DEFAULT_PLAYER_EXPIRE)
		player_data = json.dumps(player)

		self.redis.setex(player_key,    player_expire, player_data)
		self.redis.setex(player_key_id, player_expire, player['allyCode'])

	def cache_guild(self, guild):

		guild_key = 'guild|%s' % guild['id']
		guild_expire = timedelta(hours=DEFAULT_GUILD_EXPIRE)
		guild_data = json.dumps(guild)

		self.redis.setex(guild_key, guild_expire, guild_data)

	async def swgohhelp_guilds(self, selectors):

		for i in range(0, 3):

			try:
				return await api_swgoh_guilds(self.config, { 'allycodes': selectors })

			except SwgohHelpException as err:
				self.logger.error('Failed retrieving guilds with selectors: %s' % selectors)
				self.logger.error(err)
				pass

			await asyncio.sleep(1)

		return None

	async def fetch_guild(self, selector, guild=None):

		if guild is None:
			guilds = await self.swgohhelp_guilds([ selector ])
			if not guilds:
				self.logger.warning('swgohhelp_guilds failed with selector: %s' % selector)
				return None

			guild = guilds[0]

		player = await self.get_player(selector)
		if player:
			guild['id'] = player['guildRefId']
			self.cache_guild(guild)

		return guild

	async def fetch_guilds(self, selectors):

		if not selectors:
			self.logger.error('fetch_guilds got no selector')
			return {}

		guilds = await self.swgohhelp_guilds(selectors)
		if not guilds:
			self.logger.error('swgohhelp_guilds failed with selectors: %s' % selectors)
			return {}

		guilds = PremiumGuild.guilds_to_dict(selectors, guilds)

		for selector in selectors:
			guild = guilds[selector]
			await self.fetch_guild(selector, guild)

		return guilds

	async def get_guild(self, selector, fetch=True):

		player = await self.get_player(selector)
		if not player:
			self.logger.warning('get_player failed with selector: %s' % selector)
			return None

		if 'guildRefId' not in player:
			self.logger.warning('Key \'guildRefId\' missing from player profile: %s' % selector)
			return None

		guild_key = 'guild|%s' % player['guildRefId']
		guild = self.redis.get(guild_key)
		if guild:
			return json.loads(guild.decode('utf-8'))

		if fetch is True:
			return await self.fetch_guild(selector)

		return None

	async def get_guilds(self, selectors):

		guilds = {}
		to_fetch = []

		for selector in selectors:

			guild = await self.get_guild(selector, fetch=False)
			if not guild:
				to_fetch.append(selector)
				continue

			guilds[selector] = guild

		guilds.update(await self.fetch_guilds(to_fetch))

		return guilds

	async def get_selectors_to_refresh(self):

		selectors = []

		ally_codes = [ str(guild.ally_code) for guild in self.guilds ]
		for ally_code in ally_codes:

			player = await self.get_player(ally_code)
			if not player:
				selectors.append(ally_code)
				continue

			guild_key = 'guild|%s' % player['guildRefId']
			if not self.redis.exists(guild_key):
				selectors.append(ally_code)
				continue

			expire = self.redis.ttl(guild_key)
			if expire < SAFETY_TTL:
				selectors.append(ally_code)
				continue

		return selectors

	async def run(self):

		print("Starting crawler thread.")
		print('Crawler bot ready!')

		self.differ = CrawlerDiffer(self)
		self.session = await libswgoh.get_auth_guest()

		while True:

			time_start = datetime.now()

			self.guilds = list(PremiumGuild.objects.all())

			guild_selectors = [ guild.ally_code  for guild in self.guilds ]
			guild_channels  = [ guild.channel_id for guild in self.guilds ]

			selectors = await self.get_selectors_to_refresh()
			if selectors:
				await self.get_guilds(selectors)

			failed_ac, failed_ch = await self.refresh_players(guild_selectors, guild_channels)

			if failed_ac:
				failed_ac2, failed_ch2 = await self.refresh_players(failed_ac, failed_ch, selectors_only=True)
				if failed_ac2:
					self.logger.error('Could not fetch profiles after multiple attempts:\n%s' % '\n'.join(failed_ac2))
				else:
					self.logger.info('Retrieved previously failed profiles:\n%s' % '\n'.join(failed_ac))

			delta = datetime.now() - time_start
			delay = max(0, (10 * MINUTE) - delta.total_seconds())

			self.logger.debug('Sleeping for %s seconds' % delay)

			await asyncio.sleep(delay)

if __name__ == '__main__':

	import logging
	from config import load_config, setup_logs

	logger = setup_logs('crawler', 'logs/crawler.log', logging.DEBUG)

	config = load_config()

	try:
		crawler = Crawler()
		crawler.config = config
		crawler.redis = config.redis
		crawler.logger = logger

		asyncio.get_event_loop().run_until_complete(crawler.run())

	except SwgohHelpException as err:
		print(err)
		print(err.data)

	except:
		print(traceback.format_exc())
