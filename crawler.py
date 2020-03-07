#!/usr/bin/env python3

import sys
import json
import redis
import asyncio
import discord
import jsondiff
from datetime import datetime, timedelta

import DJANGO
from swgoh.models import BaseUnitSkill

import libswgoh
from utils import translate
from constants import ROMAN
from swgohhelp import fetch_guilds, get_unit_name, get_ability_name

JSON_INDENT = 4
MAX_SKILL_TIER = 8

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

		lang = 'eng_us'
		old_roster = old_profile['roster']

		old_player_name = old_profile['profile']['name']
		new_player_name = new_profile['profile']['name']
		if old_player_name != new_player_name:
			msg = '**%s** has changed nickname to **%s**' % (old_player_name, new_player_name)
			messages.append(('nicks', msg))

		for base_id, new_unit in new_profile['roster'].items():

			unit_name = get_unit_name(base_id, lang)

			# Handle new units unlocked.

			if base_id not in old_roster:
				msg = '**%s** unlocked **%s**' % (new_player_name, unit_name)
				messages.append(('unlock-unit', msg))
				continue

			# Handle unit level increase.
			
			old_level = old_roster[base_id]['level']
			new_level = new_unit['level']
			if old_level < new_level:
				msg = '**%s** promoted **%s** to level %d' % (new_player_name, unit_name, new_level)
				messages.append(('unit-level', msg))

			# Handle unit rarity increase.

			old_rarity = old_roster[base_id]['rarity']
			new_rarity = new_unit['rarity']
			if old_rarity < new_rarity:
				msg = '**%s** promoted **%s** to %d stars' % (new_player_name, unit_name, new_rarity)
				messages.append(('rarity', msg))

			# Handle gear level increase.

			old_gear_level = old_roster[base_id]['gear']
			new_gear_level = new_unit['gear']
			if old_gear_level < new_gear_level:
				roman_gear = ROMAN[new_gear_level]
				msg = '**%s** increased **%s**\'s gear to level %s' % (new_player_name, unit_name, roman_gear)
				messages.append(('gear-level', msg))

			# Handle relic increase.

			old_relic = self.get_relic(old_roster[base_id])
			new_relic = self.get_relic(new_unit)
			if old_relic < new_relic:
				msg = '**%s** increased **%s** to relic %d' % (new_player_name, unit_name, new_relic)
				messages.append(('relics', msg))

			# TODO Handle when there was a gear level change because in that case we need to do things differently
			old_equipped = old_roster[base_id]['equipped']
			new_equipped = new_unit['equipped']
			diff_equipped = [ x for x in new_equipped if x not in old_equipped ]
			if diff_equipped:
				for gear in diff_equipped:
					gear_name = translate(gear['equipmentId'], lang)
					msg = '**%s** set **%s** on **%s**' % (new_player_name, gear_name, unit_name)
					messages.append(('gear-piece', msg))

			old_skills = { x['id']: x for x in old_roster[base_id]['skills'] }
			new_skills = { x['id']: x for x in new_unit['skills'] }

			for new_skill_id, new_skill in new_skills.items():

				skill_name = get_ability_name(new_skill_id, lang)

				if new_skill_id not in old_skills:
					msg = '**%s** unlocked new skill **%s** for **%s**' % (new_player_name, skill_name, unit_name)
					messages.append(('unlock-skill', msg))
					continue

				old_skill = old_skills[new_skill_id]

				if 'tier' not in old_skill:
					old_skill['tier'] = 0

				if 'tier' not in new_skill:
					new_skill['tier'] = 0

				if old_skill['tier'] < new_skill['tier']:

					if new_skill['tier'] >= MAX_SKILL_TIER:

						try:
							unit_skill = BaseUnitSkill.objects.get(skill_id=new_skill_id)
							if unit_skill.is_zeta:
								msg = '**%s** applied Zeta upgrade **%s** (**%s**)' % (new_player_name, skill_name, unit_name)
								messages.append(('zetas', msg))

							else:
								msg = '**%s** applied Omega upgrade **%s** (**%s**)' % (new_player_name, skill_name, unit_name)
								messages.append(('omegas', msg))

						except BaseUnitSkill.DoesNotExist:
							print('ERROR: Could not find base unit skill with skill ID: %s' % new_skill_id)
					else:
						msg = '**%s** increased skill **%s** for **%s** to tier %d' % (new_player_name, skill_name, unit_name, new_skill['tier'])
						messages.append(('skill-increase', msg))

	def check_diff_player_level(self, old_profile, new_profile, messages):

		try:
			new_player_level = new_profile['profile']['level']
			old_player_level = old_profile['profile']['level']

			if old_player_level < new_player_level:
				msg = 'Player %s reached level %d' % (profile['profile']['name'], new_player_level)
				messages.append(('player-level', msg))

		except Exception as err:
			print('ERROR: check_diff_player_level: %s' % err)

	def check_last_seen(self, new_profile, messages):

		now = datetime.now()
		profile = new_profile['profile']
		updated = int(profile['updated'])
		last_sync = datetime.fromtimestamp(updated / 1000)
		delta = now - last_sync
		hours = LAST_SEEN_MAX_HOURS
		if delta > timedelta(hours=hours):

			ally_code = profile['allyCode']
			if ally_code in self.last_notify:
				last_notify = self.last_notify[ally_code]
				diff_to_now = now - last_notify
				if diff_to_now < timedelta(hours=LAST_SEEN_MAX_HOURS_INTERVAL):
					return

			self.last_notify[ally_code] = now
			last_activity = delta - timedelta(microseconds=delta.microseconds)
			msg = '**%s** has been inactive for **%s**' % (profile['name'], last_activity)
			messages.append(('inactivity', msg))

	def check_diff(self, old_profile, new_profile):

		messages = []

		self.check_diff_player_level(old_profile, new_profile, messages)

		self.check_diff_player_units(old_profile, new_profile, messages)

		self.check_last_seen(new_profile, messages)

		return messages
		
	def update_player(self, ally_code, profile, channel_id):

		if 'name' not in profile:
			print('Failed retrieving profile for allycode %s' % ally_code)
			return []

		roster = {}
		if 'roster' in profile:
			roster = { x['defId']: x for x in profile['roster'] }

		new_profile = {
			'profile': profile,
			'roster': roster,
		}

		player_key = 'player|%s' % ally_code
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
			for tag, message in messages:
				formated.append('|'.join([ tag, message ]))

			messages_key = 'messages|%s' % channel_id
			self.redis.rpush(messages_key, *formated)

	async def refresh_guild(self, ally_code):

		guild_key = 'guild|%s' % ally_code
		expire = timedelta(hours=DEFAULT_GUILD_EXPIRE)
		guild = await fetch_guilds(config, [ ally_code ])
		guild_data = json.dumps(guild, indent=JSON_INDENT)

		self.redis.setex(guild_key, expire, guild_data)

		return guild

	async def refresh_guilds(self, ally_codes):

		guilds = await fetch_guilds(config, ally_codes)
		for allycode, guild in guilds.items():
			guild_key = 'guild|%s' % allycode
			expire = timedelta(hours=DEFAULT_GUILD_EXPIRE)
			self.redis.setex(guild_key, expire, json.dumps(guild))

		return guilds

	def get_allycodes_to_refresh(self):

		needed = []
		ally_codes = [ guild[0] for guild in self.guilds ]
		for ally_code in ally_codes:
			guild_key = 'guild|%s' % ally_code
			if not self.redis.exists(guild_key):
				needed.append(ally_code)
				continue

			expire = self.redis.ttl(guild_key)
			if expire < SAFETY_TTL:
				needed.append(ally_code)

		return needed

	async def run(self, crawler, guilds):

		self.guilds = guilds
		self.redis = redis.Redis()
		session = await libswgoh.get_auth_guest()

		ally_codes = [ guild[0] for guild in guilds ]
		channels   = [ guild[1] for guild in guilds ]

		while True:

			to_refresh = self.get_allycodes_to_refresh()
			if to_refresh:
				await self.refresh_guilds(to_refresh)

			print(datetime.now())
			for ally_code, channel in zip(ally_codes, channels):

				guild_key = 'guild|%s' % ally_code
				guild = self.redis.get(guild_key)
				if guild:
					guild = json.loads(guild.decode('utf-8'))
				else:
					guild = await self.refresh_guild(ally_code)

				for ally_code, member in guild['roster'].items():

					profile = await libswgoh.get_player_profile(ally_code=ally_code, session=session)
					if not profile:
						print('Failed retrieving profile for %s, skipping.' % ally_code)
						continue

					# TODO: Fix this atrocity
					profile = json.loads(json.dumps(profile))

					self.update_player(ally_code, profile, channel)

			await asyncio.sleep(1)

class Crawler(discord.Client):

	guilds = [
		('349423868', 575654803099746325),
		('913624995', 548533152386121763),
	]

	async def on_ready(self):

		if not hasattr(self, 'initialized'):
			setattr(self, 'initialized', True)
			print("Starting crawler thread.")
			self.loop.create_task(CrawlerThread().run(self, self.guilds))

		print('Crawler bot ready!')

if __name__ == '__main__':

	import logging
	logging.basicConfig(level=logging.INFO)

	from config import load_config
	config = load_config()

	Crawler().run(config['tokens']['crawler'])
