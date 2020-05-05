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
	#creds_id = 'reverseswgoh@gmail.com'

	def redis_get(self, key):
		value = self.redis.get(key)
		return value and json.loads(value.decode('utf-8')) or None

	async def update_player(self, guild, player_id, restart=True):

		profile = None
		try:
			profile = await self.client.player(player_id=player_id, session=self.session, no_cache=True)

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
		old_profile = self.redis_get(player_key)
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

		self.logger.debug('%s - %s' % (guild.guild_id, player_id))

	async def refresh_players(self, selectors, channels, selectors_only=False):

		failed_ac = []
		failed_ch = []

		for selector, channel in zip(selectors, channels):

			guild = await self.client.guild(selector=selector, session=self.session)
			if not guild:
				print('Guild not found in redis for selector: %s' % selector)
				continue

			if selectors_only is False:
				print('Crawling guild %s - %s' % (guild['id'], guild['name']))
				#print(json.dumps(guild, indent=4))

			premium_guild = PremiumGuild.get_guild(guild['id'])
			if not premium_guild:
				print('Guild not found in redis: %s (selector: %s)' % (guild['id'], selector))
				continue

			for member in guild['roster']:

				if selectors_only is True and member['playerId'] not in selectors:
					continue

				try:
					await self.update_player(premium_guild, member['playerId'])

				except CrawlerError:

					print(traceback.format_exc())
					failed_ac.append(member['playerId'])
					failed_ch.append(channel)

				except Exception as err:
					print(traceback.format_exc())

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

	async def run(self):

		print("Starting crawler thread.")
		print('Crawler bot ready!')

		self.differ = CrawlerDiffer(self)
		self.session = await libswgoh.get_auth_google(creds_id=self.creds_id)

		while True:

			time_start = datetime.now()

			self.guilds = list(PremiumGuild.objects.all())

			guild_selectors = [ guild.selector   for guild in self.guilds ]
			guild_channels  = [ guild.channel_id for guild in self.guilds ]

			print('Pass 1')
			failed_ac, failed_ch = await self.refresh_players(guild_selectors, guild_channels)

			if failed_ac:
				print('Pass 2')
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

		from client import SwgohClient
		crawler.client = SwgohClient(crawler)

		asyncio.get_event_loop().run_until_complete(crawler.run())

	except libswgoh.LibSwgohException as err:
		print(err)
		print(err.data)

	except:
		print(traceback.format_exc())
