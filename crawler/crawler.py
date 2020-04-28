#!/usr/bin/env python3

import sys
import json
import asyncio
import traceback
from datetime import datetime, timedelta

from constants import MINUTE

import DJANGO
from swgoh.models import PremiumGuild

from crawlerdiffer import CrawlerDiffer

import libswgoh
import protos.swgoh_pb2 as swgoh_pb2

SAFETY_TTL = 10 * MINUTE

DEFAULT_GUILD_EXPIRE = 24
DEFAULT_PLAYER_EXPIRE = 24

class CrawlerError(Exception):
	pass

class Crawler(asyncio.Future):

	creds_id = None
	#creds_id = 'anraeth'

	async def update_player(self, guild, player_id, restart=True):

		profile = None
		try:
			profile = await libswgoh.get_player_profile(player_id=player_id, session=self.session)

		except libswgoh.LibSwgohException as err:
			if err.response.code == swgoh_pb2.ResponseCode.AUTHFAILED:
				self.session = await libswgoh.get_auth_google(creds_id=self.creds_id)
				if restart is True:
					return await self.update_player(guild, player_id, restart=False)

		if not profile:
			msg = 'Failed retrieving profile for player ID %s, skipping.' % player_id
			self.logger.error(msg)
			raise CrawlerError(msg)

		# TODO: Fix this atrocity
		profile = json.loads(json.dumps(profile))

		if 'name' not in profile:
			self.logger.warning('Failed retrieving profile for player ID %s' % player_id)
			return []

		#if 'roster' in profile:
		#	profile['roster'] = { x['defId']: x for x in profile['roster'] }

		player_key = 'player|%s' % player_id
		new_profile = profile
		old_profile = await self.get_player(player_id, fetch=False)
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

		self.logger.debug(player_id)

	async def get_player(self, player_id, fetch=True, restart=True):

		key = 'player|%s' % player_id
		profile = self.redis.get(key)
		if profile:
			return json.loads(profile.decode('utf-8'))

		try:
			profile = await libswgoh.get_player_profile(player_id=player_id, session=self.session)

		except libswgoh.LibSwgohException as err:
			if err.response.code == swgoh_pb2.ResponseCode.AUTHFAILED:
				self.session = await libswgoh.get_auth_google(creds_id=self.creds_id)
				if restart is True:
					return await self.get_player(player_id, fetch=fetch, restart=False)

		if profile:
			id_key = 'playerid|%s' % profile['allyCode']
			expire = timedelta(hours=DEFAULT_PLAYER_EXPIRE)
			self.redis.setex(key, expire, json.dumps(profile))
			self.redis.setex(id_key, expire, player_id)

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

				if selectors_only is True and member['playerId'] not in selectors:
					continue

				try:
					await self.update_player(premium_guild, member['playerId'])

				except CrawlerError:
					# Don't print stacktrace for CrawlerError
					pass

				except Exception as err:
					print(traceback.format_exc())

				finally:
					failed_ac.append(member['playerId'])
					failed_ch.append(channel)

		return failed_ac, failed_ch

	def cache_player(self, player):

		player_key = 'player|%s' % player['id']
		player_key_id = 'playerid|%s' % player['allyCode']
		player_expire = timedelta(hours=DEFAULT_PLAYER_EXPIRE)
		player_data = json.dumps(player)

		self.redis.setex(player_key,    player_expire, player_data)
		self.redis.setex(player_key_id, player_expire, player['id'])

	def cache_guild(self, guild):

		guild_key = 'guild|%s' % guild['id']
		guild_expire = timedelta(hours=DEFAULT_GUILD_EXPIRE)
		guild_data = json.dumps(guild)

		self.redis.setex(guild_key, guild_expire, guild_data)

	async def libswgoh_guilds(self, selectors):

		for i in range(0, 3):

			try:
				return await libswgoh.get_guilds(selectors=selectors, session=self.session)

			except libswgoh.LibSwgohException as err:
				self.logger.error('Failed retrieving guilds with selectors: %s' % selectors)
				self.logger.error(err)
				pass

			await asyncio.sleep(1)

		return None

	async def fetch_guild(self, selector, guild=None):

		if guild is None:
			guilds = await libswgoh.get_guilds(selectors=[ selector ], session=self.session)
			if not guilds:
				self.logger.warning('libswgoh.get_guilds failed with selector: %s' % selector)
				return None

			guild = guilds[selector]

		player = await self.get_player(selector)
		if player:
			guild['id'] = player['guildRefId']
			self.cache_guild(guild)

		return guild

	async def fetch_guilds(self, selectors):

		if not selectors:
			self.logger.error('fetch_guilds got no selector')
			return {}

		guilds = await libswgoh.get_guilds(selectors=selectors, session=self.session)
		if not guilds:
			self.logger.error('libswgoh.get_guilds failed with selectors: %s' % selectors)
			return {}

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

		guild_selectors = [ guild.selector for guild in self.guilds ]
		for selector in guild_selectors:

			player = await self.get_player(selector)
			if not player:
				selectors.append(selector)
				continue

			guild_key = 'guild|%s' % player['guildRefId']
			if not self.redis.exists(guild_key):
				selectors.append(selector)
				continue

			expire = self.redis.ttl(guild_key)
			if expire < SAFETY_TTL:
				selectors.append(selector)
				continue

		return selectors

	async def run(self):

		print("Starting crawler thread.")
		print('Crawler bot ready!')

		self.differ = CrawlerDiffer(self)
		self.session = await libswgoh.get_auth_google(creds_id=creds_id)

		while True:

			time_start = datetime.now()

			self.guilds = list(PremiumGuild.objects.all())

			guild_selectors = [ guild.selector   for guild in self.guilds ]
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

			await asyncio.sleep(1)

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

	except libswgoh.LibSwgohException as err:
		print(err)
		print(err.data)

	except:
		print(traceback.format_exc())
