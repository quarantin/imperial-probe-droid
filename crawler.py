#!/usr/bin/env python3

import sys
import json
import asyncio
import discord
import libswgoh
import traceback
from datetime import datetime, timedelta

from constants import MAX_SKILL_TIER, MINUTE
from swgohhelp import api_swgoh_guilds, SwgohHelpException

import DJANGO
from swgoh.models import PremiumGuild, PremiumGuildConfig

SAFETY_TTL = 10 * MINUTE

DEFAULT_GUILD_EXPIRE = 24
DEFAULT_PLAYER_EXPIRE = 24

class CrawlerThread(asyncio.Future):

	def get_relic(self, unit):

		if 'relic' in unit and unit['relic'] and 'currentTier' in unit['relic']:
			return max(0, unit['relic']['currentTier'] - 2)

		return 0

	def check_diff_player_units(self, guild, old_profile, new_profile, messages):

		old_roster = { x['defId']: x for x in old_profile['roster'] }
		new_roster = { x['defId']: x for x in new_profile['roster'] }

		old_player_name = old_profile['name']
		new_player_name = new_profile['name']
		if old_player_name != new_player_name:
			messages.append({
				'key': PremiumGuildConfig.MSG_PLAYER_NICK,
				'nick': old_player_name,
				'new.nick': new_player_name,
			})

		for base_id, new_unit in new_roster.items():

			# Handle new units unlocked.
			if base_id not in old_roster:
				messages.append({
					'key': PremiumGuildConfig.MSG_UNIT_UNLOCKED,
					'nick': new_player_name,
					'unit': base_id,
				})
				continue

			# Handle unit level increase.
			old_level = old_roster[base_id]['level']
			new_level = new_unit['level']
			if old_level < new_level:
				messages.append({
					'key': PremiumGuildConfig.MSG_UNIT_LEVEL,
					'nick': new_player_name,
					'unit': base_id,
					'level': new_level,
				})

			# Handle unit rarity increase.
			old_rarity = old_roster[base_id]['rarity']
			new_rarity = new_unit['rarity']
			if old_rarity < new_rarity:
				messages.append({
					'key': PremiumGuildConfig.MSG_UNIT_RARITY,
					'nick': new_player_name,
					'unit': base_id,
					'rarity': new_rarity,
				})

			# Handle gear level increase.
			old_gear_level = old_roster[base_id]['gear']
			new_gear_level = new_unit['gear']
			if old_gear_level < new_gear_level:
				messages.append({
					'key': PremiumGuildConfig.MSG_UNIT_GEAR_LEVEL,
					'nick': new_player_name,
					'unit': base_id,
					'gear.level': new_gear_level,
				})

			# Handle relic increase.
			old_relic = self.get_relic(old_roster[base_id])
			new_relic = self.get_relic(new_unit)
			if old_relic < new_relic:
				messages.append({
					'key': PremiumGuildConfig.MSG_UNIT_RELIC,
					'nick': new_player_name,
					'unit': base_id,
					'relic': new_relic,
				})

			# TODO Handle case when there was a gear level change because in that case we need to do things differently
			old_equipped = old_roster[base_id]['equipped']
			new_equipped = new_unit['equipped']
			diff_equipped = [ x for x in new_equipped if x not in old_equipped ]
			if diff_equipped:
				for gear in diff_equipped:
					messages.append({
						'key': PremiumGuildConfig.MSG_UNIT_GEAR_PIECE,
						'nick': new_player_name,
						'unit': base_id,
						'gear.piece': gear['equipmentId']
					})

			old_skills = { x['id']: x for x in old_roster[base_id]['skills'] }
			new_skills = { x['id']: x for x in new_unit['skills'] }

			for new_skill_id, new_skill in new_skills.items():

				if new_skill_id not in old_skills:
					messages.append({
						'key': PremiumGuildConfig.MSG_UNIT_SKILL_UNLOCKED,
						'nick': new_player_name,
						'unit': base_id,
						'skill': new_skill_id,
					})
					continue

				old_skill = old_skills[new_skill_id]

				if 'tier' not in old_skill:
					old_skill['tier'] = 0

				if 'tier' not in new_skill:
					new_skill['tier'] = 0

				if old_skill['tier'] < new_skill['tier']:

					messages.append({
						'key': PremiumGuildConfig.MSG_UNIT_SKILL_INCREASED,
						'nick': new_player_name,
						'unit': base_id,
						'skill': new_skill_id,
						'tier': new_skill['tier']
					})

	def check_diff_player_level(self, guild, old_profile, new_profile, messages):

		new_player_level = new_profile['level']
		old_player_level = old_profile['level']

		if old_player_level < new_player_level:
			messages.append({
				'key': PremiumGuildConfig.MSG_PLAYER_LEVEL,
				'nick': new_profile['name'],
				'level': new_player_level,
			})

	def check_diff_arena_ranks(self, guild, old_profile, new_profile, messages):

		for arena_type in [ 'char', 'ship' ]:

			old_rank = old_profile['arena'][arena_type]['rank']
			new_rank = new_profile['arena'][arena_type]['rank']

			key = None
			if old_rank < new_rank:
				key = (arena_type == 'char') and PremiumGuildConfig.MSG_SQUAD_ARENA_DOWN or PremiumGuildConfig.MSG_FLEET_ARENA_DOWN

			elif old_rank > new_rank:
				key = (arena_type == 'char') and PremiumGuildConfig.MSG_SQUAD_ARENA_UP or PremiumGuildConfig.MSG_FLEET_ARENA_UP

			if key:
				messages.append({
					'key': key,
					'type': arena_type,
					'nick': new_profile['name'],
					'old.rank': old_rank,
					'new.rank': new_rank
				})

	def check_last_seen(self, guild, new_profile, messages):

		config = guild.get_config()
		last_seen_max = config[PremiumGuildConfig.MSG_INACTIVITY_MIN]
		last_seen_interval = config[PremiumGuildConfig.MSG_INACTIVITY_REPEAT]

		profile = new_profile
		updated = int(profile['updated'])
		last_sync = datetime.fromtimestamp(updated / 1000)
		delta = datetime.now() - last_sync
		if delta > timedelta(hours=last_seen_max):

			inactivity_key = 'inactivity|%s' % profile['allyCode']
			expire = timedelta(hours=last_seen_interval)

			value = self.redis.get(inactivity_key)
			if value:
				return

			self.redis.setex(inactivity_key, expire, 1)

			last_activity = str(delta - timedelta(microseconds=delta.microseconds))
			messages.append({
				'key': PremiumGuildConfig.MSG_INACTIVITY,
				'nick': profile['name'],
				'last.seen': last_activity,
			})

	def check_diff(self, guild, old_profile, new_profile):

		messages = []

		self.check_diff_arena_ranks(guild, old_profile, new_profile, messages)

		self.check_diff_player_level(guild, old_profile, new_profile, messages)

		self.check_diff_player_units(guild, old_profile, new_profile, messages)

		self.check_last_seen(guild, new_profile, messages)

		return messages

	async def update_player(self, guild, ally_code):

		ally_code = str(ally_code)
		profile = await libswgoh.get_player_profile(ally_code=ally_code, session=self.session)
		if not profile:
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
		if old_profile is None:
			old_profile = new_profile

		messages = self.check_diff(guild, old_profile, new_profile)

		self.cache_player(new_profile)

		if messages:

			formated = []
			for message in messages:
				formated.append(json.dumps(message))

			messages_key = 'messages|%s' % guild.guild_id
			self.redis.rpush(messages_key, *formated)

	async def get_player(self, ally_code, fetch=True):

		key = 'player|%s' % ally_code
		profile = self.redis.get(key)
		if profile:
			return json.loads(profile.decode('utf-8'))

		profile = await libswgoh.get_player_profile(ally_code=ally_code, session=self.session)
		if profile:
			expire = timedelta(hours=DEFAULT_PLAYER_EXPIRE)
			self.redis.setex(key, expire, json.dumps(profile))

		return profile

	async def refresh_players(self, selectors, channels, selectors_only=False):

		failed_ac = []
		failed_ch = []

		for selector, channel in zip(selectors, channels):

			guild = await self.get_guild(selector)
			if not guild:
				self.logger.warning('Guild not found in redis: %s' % selector)
				continue

			premium_guild = PremiumGuild.get_guild(guild['id'])
			if not premium_guild:
				self.logger.warning('Guild not found in redis: %s' % guild['id'])
				continue

			for member in guild['roster']:

				if selectors_only is True and str(member['allyCode']) not in selectors:
					continue

				try:
					await self.update_player(premium_guild, member['allyCode'])

				except:
					failed_ac.append(allycode)
					failed_ch.append(channel)

		return failed_ac, failed_ch

	def cache_player(self, player):

		player_key = 'player|%s' % player['allyCode']
		player_expire = timedelta(hours=DEFAULT_PLAYER_EXPIRE)
		player_data = json.dumps(player)

		self.redis.setex(player_key, player_expire, player_data)

	def cache_guild(self, guild):

		guild_key = 'guild|%s' % guild['id']
		guild_expire = timedelta(hours=DEFAULT_GUILD_EXPIRE)
		guild_data = json.dumps(guild)

		self.redis.setex(guild_key, guild_expire, guild_data)

	async def fetch_guild(self, selector, guild=None):

		if guild is None:
			guilds = await api_swgoh_guilds(self.config, { 'allycodes': [ selector ] })
			guild = guilds[0]

		player = await self.get_player(selector)
		guild['id'] = player['guildRefId']
		self.cache_guild(guild)
		return guild

	async def fetch_guilds(self, selectors):

		guilds = await api_swgoh_guilds(self.config, { 'allycodes': selectors })
		guilds = PremiumGuild.guilds_to_dict(selectors, guilds)

		for selector in selectors:
			guild = guilds[selector]
			await self.fetch_guild(selector, guild)

		return guilds

	async def get_guild(self, selector, fetch=True):

		player = await self.get_player(selector)

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

	async def get_allycodes_to_refresh(self):

		to_refresh = []

		ally_codes = [ str(guild.ally_code) for guild in self.guilds ]
		for ally_code in ally_codes:

			player = await self.get_player(ally_code)
			if not player:
				to_refresh.append(ally_code)
				continue

			guild_key = 'guild|%s' % player['guildRefId']
			if not self.redis.exists(guild_key):
				to_refresh.append(ally_code)
				continue

			expire = self.redis.ttl(guild_key)
			if expire < SAFETY_TTL:
				to_refresh.append(ally_code)
				continue

		return to_refresh

	async def run(self, bot):

		self.bot = bot
		self.logger = bot.logger
		self.config = bot.config
		self.redis = bot.redis
		self.session = await libswgoh.get_auth_guest()

		while True:

			self.guilds = list(PremiumGuild.objects.all())

			guild_selectors = PremiumGuild.get_guild_selectors()
			channels = [ guild.channel_id for guild in self.guilds ]

			to_refresh = await self.get_allycodes_to_refresh()
			if to_refresh:
				await self.get_guilds(to_refresh)

			time_start = datetime.now()
			failed_ac, failed_ch = await self.refresh_players(guild_selectors, channels)

			if failed_ac:
				failed_ac2, failed_ch2 = await self.refresh_players(failed_ac, failed_ch, selectors_only=True)
				if failed_ac2:
					self.logger.error('Could not fetch profiles after multiple attempts:\n%s' % '\n'.join(failed_ac2))
				else:
					self.logger.info('Retrieved previously failed profiles:\n%s' % '\n'.join(failed_ac))

			diff = datetime.now() - time_start
			delay = max(0, (10 * MINUTE) - diff.total_seconds())

			self.logger.debug('Sleeping for %s seconds' % delay)

			await asyncio.sleep(delay)

class Crawler(discord.Client):

	async def on_ready(self):

		if not hasattr(self, 'initialized'):
			setattr(self, 'initialized', True)
			print("Starting crawler thread.")
			self.loop.create_task(CrawlerThread().run(self))

		print('Crawler bot ready!')

if __name__ == '__main__':

	import logging
	from config import load_config, setup_logs

	crawler_logger = setup_logs('crawler', 'logs/crawler.log', logging.DEBUG)
	discord_logger = setup_logs('discord', 'logs/crawler-discord.log')

	config = load_config()

	if 'tokens' not in config:
		print('Key "tokens" missing from config %s' % config_file, file=sys.stderr)
		sys.exit(-1)

	if 'crawler' not in config['tokens']:
		print('Key "crawler" missing from config %s' % config_file, file=sys.stderr)
		sys.exit(-1)

	try:
		crawler = Crawler()
		crawler.config = config
		crawler.redis = config.redis
		crawler.logger = crawler_logger
		crawler.run(config['tokens']['crawler'])

	except SwgohHelpException as err:
		print(err)
		print(err.data)

	except:
		print(traceback.format_exc())
