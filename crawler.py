#!/usr/bin/env python3

import sys
import json
import redis
import asyncio
import discord
import libswgoh
import traceback
from datetime import datetime, timedelta

from constants import MAX_SKILL_TIER
from swgohhelp import api_swgoh_guilds

import DJANGO
from swgoh.models import PremiumGuild, PremiumGuildConfig

JSON_INDENT = None # 4

LAST_SEEN_MAX_HOURS = 48
LAST_SEEN_MAX_HOURS_INTERVAL = 24

SAFETY_TTL = 3600

DEFAULT_GUILD_EXPIRE = 24
DEFAULT_PLAYER_EXPIRE = 24

class CrawlerThread(asyncio.Future):

	def get_relic(self, unit):

		if 'relic' in unit and unit['relic'] and 'currentTier' in unit['relic']:
			return max(0, unit['relic']['currentTier'] - 2)

		return 0

	def check_diff_player_units(self, old_profile, new_profile, messages):

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

	def check_diff_player_level(self, old_profile, new_profile, messages):

		new_player_level = new_profile['level']
		old_player_level = old_profile['level']

		if old_player_level < new_player_level:
			messages.append({
				'key': PremiumGuildConfig.MSG_PLAYER_LEVEL,
				'nick': new_profile['name'],
				'level': new_player_level,
			})

	def check_diff_arena_ranks(self, old_profile, new_profile, messages):

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

	def check_last_seen(self, new_profile, messages):

		now = datetime.now()
		profile = new_profile
		updated = int(profile['updated'])
		last_sync = datetime.fromtimestamp(updated / 1000)
		delta = now - last_sync
		if delta > timedelta(hours=LAST_SEEN_MAX_HOURS):

			ally_code = profile['allyCode']
			if ally_code in self.last_notify:
				last_notify = self.last_notify[ally_code]
				diff_to_now = now - last_notify
				if diff_to_now < timedelta(hours=LAST_SEEN_MAX_HOURS_INTERVAL):
					return

			self.last_notify[ally_code] = now
			last_activity = str(delta - timedelta(microseconds=delta.microseconds))
			messages.append({
				'key': PremiumGuildConfig.MSG_INACTIVITY,
				'nick': profile['name'],
				'last.seen': last_activity,
			})

	def check_diff(self, old_profile, new_profile):

		messages = []

		self.check_diff_arena_ranks(old_profile, new_profile, messages)

		self.check_diff_player_level(old_profile, new_profile, messages)

		self.check_diff_player_units(old_profile, new_profile, messages)

		self.check_last_seen(new_profile, messages)

		return messages

	async def ensure_player(self, ally_code):

		key = 'player|%s' % ally_code
		profile = self.redis.get(ally_code)
		if not profile:
			profile = await libswgoh.get_player_profile(ally_code=ally_code, session=self.session)
			if profile:
				expire = timedelta(hours=DEFAULT_PLAYER_EXPIRE)
				self.redis.setex(key, expire, json.dumps(profile, indent=JSON_INDENT))

		return profile

	async def update_player(self, ally_code, guild_id):

		ally_code = str(ally_code)
		profile = await libswgoh.get_player_profile(ally_code=ally_code, session=self.session)
		if not profile:
			print('Failed retrieving profile for %s, skipping.' % ally_code)
			return []

		# TODO: Fix this atrocity
		profile = json.loads(json.dumps(profile))

		if 'name' not in profile:
			print('Failed retrieving profile for allycode %s' % ally_code)
			return []

		#if 'roster' in profile:
		#	profile['roster'] = { x['defId']: x for x in profile['roster'] }

		player_key = 'player|%s' % ally_code
		new_profile = profile
		old_profile = self.redis.get(player_key)
		if old_profile is None:
			old_profile = new_profile
		else:
			old_profile = json.loads(old_profile.decode('utf-8'))

		messages = self.check_diff(old_profile, new_profile)

		expire = timedelta(hours=DEFAULT_PLAYER_EXPIRE)
		profile_data = json.dumps(new_profile, indent=JSON_INDENT)

		self.redis.setex(player_key, expire, profile_data)

		if messages:

			formated = []
			for message in messages:
				formated.append(json.dumps(message))

			messages_key = 'messages|%s' % guild_id
			self.redis.rpush(messages_key, *formated)

	async def refresh_guild(self, ally_code):

		player = await self.ensure_player(ally_code)

		guild_key = 'guild|%s' % player['guildRefId']
		expire = timedelta(hours=DEFAULT_GUILD_EXPIRE)
		guild = await api_swgoh_guilds(config, { 'allycodes': [ ally_code ] })
		guild_data = json.dumps(guild[0], indent=JSON_INDENT)

		self.redis.setex(guild_key, expire, guild_data)

		return guild[0]

	async def refresh_guilds(self, ally_codes):

		for ally_code in ally_codes:
			await self.refresh_guild(ally_code)

	async def get_allycodes_to_refresh(self):

		needed = []
		ally_codes = [ str(guild.ally_code) for guild in self.guilds ]
		for ally_code in ally_codes:
			player = await self.ensure_player(ally_code)
			guild_key = 'guild|%s' % player['guildRefId']
			if not self.redis.exists(guild_key):
				needed.append(ally_code)
				continue

			expire = self.redis.ttl(guild_key)
			if expire < SAFETY_TTL:
				needed.append(ally_code)

		return needed

	async def run(self, crawler):

		self.redis = redis.Redis()
		self.session = await libswgoh.get_auth_guest()
		self.last_notify = {}

		while True:

			self.guilds = list(PremiumGuild.objects.all())

			ally_codes = [ str(guild.ally_code) for guild in self.guilds ]
			channels   = [ guild.channel_id for guild in self.guilds ]

			to_refresh = await self.get_allycodes_to_refresh()
			if to_refresh:
				await self.refresh_guilds(to_refresh)

			print(datetime.now())
			for ally_code, channel in zip(ally_codes, channels):

				player = await self.ensure_player(ally_code)
				guild_key = 'guild|%s' % player['guildRefId']
				guild = self.redis.get(guild_key)
				if guild:
					guild = json.loads(guild.decode('utf-8'))
				else:
					print('guild not found in redis')
					guild = await self.refresh_guild(ally_code)

				for member in guild['roster']:
					await self.update_player(member['allyCode'], player['guildRefId'])

			await asyncio.sleep(600)

class Crawler(discord.Client):

	async def on_ready(self):

		if not hasattr(self, 'initialized'):
			setattr(self, 'initialized', True)
			print("Starting crawler thread.")
			self.loop.create_task(CrawlerThread().run(self))

		print('Crawler bot ready!')

if __name__ == '__main__':

	from config import load_config, setup_logs

	setup_logs('discord', 'logs/crawler-discord.log')

	config = load_config()

	if 'tokens' not in config:
		print('Key "tokens" missing from config %s' % config_file, file=sys.stderr)
		sys.exit(-1)

	if 'crawler' not in config['tokens']:
		print('Key "crawler" missing from config %s' % config_file, file=sys.stderr)
		sys.exit(-1)

	try:
		Crawler().run(config['tokens']['crawler'])

	except:
		print(traceback.format_exc())
