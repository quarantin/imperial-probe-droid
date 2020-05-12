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

class AuthError(Exception):
	pass

class Crawler(asyncio.Future):

	creds_id = None
	#creds_id = 'reverseswgoh@gmail.com'

	def redis_get(self, key):
		value = self.redis.get(key)
		return value and json.loads(value.decode('utf-8')) or None

	def redis_setex(self, key, value, as_json=False):
		expire = timedelta(hours=DEFAULT_PLAYER_EXPIRE)
		redis_value = as_json is True and json.dumps(value) or value
		self.redis.setex(key, expire, redis_value)

	async def update_player(self, premium, guild, player_id):

		player_key = 'player|%s' % player_id
		old_profile = self.redis_get(player_key)

		new_profile = None
		try:
			new_profile = await self.client.player(player_id=player_id, session=self.session, no_cache=True)

		except libswgoh.LibSwgohException as err:
			if err.response.code == swgoh_pb2.ResponseCode.AUTHFAILED:
				msg = 'Sesssion expired!'
				self.logger.warning(msg)
				raise AuthError(msg)

		if new_profile is None:
			msg = 'Failed retrieving profile for player ID %s, skipping.' % player_id
			self.logger.error(msg)
			raise CrawlerError(msg)

		if 'name' not in new_profile:
			self.logger.error('Failed retrieving profile for player ID %s (incomplete)' % player_id)
			return

		messages = self.differ.check_diff(premium, guild, old_profile, new_profile)
		if messages:

			formated = []
			for message in messages:
				formated.append(json.dumps(message))

			messages_key = 'messages|%s' % guild['id']
			self.redis.rpush(messages_key, *formated)

		# Actually save profile to cache because we used no_cache=True
		playerid_key = 'playerid|%s' % new_profile['allyCode']
		self.redis_setex(player_key, new_profile, as_json=True)
		self.redis_setex(playerid_key, player_id)

		self.logger.debug('%s - %s  (%d messages)' % (guild['id'], player_id, len(messages)))

	async def refresh_guild(self, premium, guild, members):

		errors = []

		for member in members:

			try:
				await self.update_player(premium, guild, member['playerId'])
				continue

			except AuthError:
				self.session = await libswgoh.get_auth_google(creds_id=self.creds_id)

			except CrawlerError:
				pass

			except Exception as err:
				print(err)
				print(traceback.format_exc())

			errors.append(member)

		return errors

	async def run(self):

		print("Starting crawler thread.")

		crawler.session = await libswgoh.get_auth_google(creds_id=self.creds_id)

		print('Crawler bot ready!')

		while True:

			time_start = datetime.now()

			premium_guilds = list(PremiumGuild.objects.all())

			selectors = [ guild.selector for guild in premium_guilds ]

			guilds = await self.client.guilds(player_ids=selectors, session=self.session)

			for premium in premium_guilds:

				selector = premium.selector
				guild = guilds[selector]

				print('Crawling guild %s - %s' % (guild['id'], guild['name']))

				errors = await self.refresh_guild(premium, guild, guild['roster'])
				if errors:
					errors2 = await self.refresh_guild(premium, guild, errors)
					if errors2:
						self.logger.error('Could not fetch profiles after multiple attempts:\n%s' % '\n'.join([ x['playerId'] for x in errors2 ]))
					else:
						self.logger.info('Retrieved previously failed profiles:\n%s' % '\n'.join([ x['playerId'] for x in errors ]))

			delta = datetime.now() - time_start
			delay = max(0, (10 * MINUTE) - delta.total_seconds())

			self.logger.debug('Sleeping for %s seconds' % delay)

			await asyncio.sleep(1)
			#await asyncio.sleep(delay)

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
		crawler.differ = CrawlerDiffer(crawler)

		asyncio.get_event_loop().run_until_complete(crawler.run())

	except libswgoh.LibSwgohException as err:
		print(err)
		print(err.data)
		print(traceback.format_exc())

	except Exception as err:
		print(err)
		print(traceback.format_exc())
