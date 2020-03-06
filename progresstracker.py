#!/usr/bin/env python3

import sys
import json
import asyncio
import discord
import libswgoh
import libprotobuf
from utils import translate
from datetime import datetime, timedelta
from swgohhelp import get_unit_name, get_ability_name

import DJANGO
from swgoh.models import BaseUnitSkill

MAX_SKILL_TIER = 8

LAST_SEEN_MAX_HOURS = 48
LAST_SEEN_MAX_HOURS_INTERVAL = 24

ROMAN = {
	1: 'I',
	2: 'II',
	3: 'II',
	4: 'IV',
	5: 'V',
	6: 'VI',
	7: 'VII',
	8: 'VIII',
	9: 'IX',
	10: 'X',
	11: 'XI',
	12: 'XII',
	13: 'XIII',
}

my_short_guild = [
		'791187582',
		'349423868',
		'939217396',
]

my_real_guild = [
		'717952293',
		'823138241',
		'679953994',
		'285791283',
		'151522739',
		'791187582',
		'796768616',
		'963851733',
		'249146726',
		'764433286',
		'349916511',
		'313811128',
		'299618942',
		'841628554',
		'689384858',
		'432487688',
		'159773229',
		'386333955',
		'183566241',
		'939217396',
		'679624581',
		'841136222',
		'861695949',
		'788498477',
		'679283652',
		'835375258',
		'364187935',
		'919446723',
		'439553819',
		'622536847',
		'693322138',
		'721916843',
		'243118455',
		'577321579',
		'859732948',
		'423694941',
		'473387221',
		'126851788',
		'674676931',
		'275786885',
		'158895788',
		'896688629',
		'361119762',
		'349423868',
		'746734837',
	]

my_guild = {
	'channel_id': 682302185085730910,
	'members': my_real_guild,
}

def strip_text(text):
	return text.replace('**', '')

def to_colored_text(text, lang='', prefix=''):
	return '```%s\n%s %s```' % (lang, prefix, strip_text(text))

def to_color_none(text):
	return text

def to_color_default(text):
	return to_colored_text(text)

def to_color_quote(text):
	return to_colored_text(text, 'brainfuck')

def to_color_green(text):
	return to_colored_text(text, 'CSS')

def to_color_cyan(text):
	return to_colored_text(text, 'yaml')

def to_color_blue(text):
	return to_colored_text(text, 'md')

def to_color_yellow(text):
	return to_colored_text(text, 'fix')

def to_color_orange(text):
	return to_colored_text(text, 'glsl')

def to_color_red(text):
	return to_colored_text(text, 'diff', '-')

colors = {
	'default': to_color_default,
	'quote':   to_color_quote,
	'green':   to_color_green,
	'cyan':    to_color_cyan,
	'blue':    to_color_blue,
	'yellow':  to_color_yellow,
	'orange':  to_color_orange,
	'red':     to_color_red,
}

def get_color_func(msg_type):

	if msg_type == 'zetas':
		return to_color_cyan

	if msg_type == 'omegas':
		return to_color_yellow

	if msg_type == 'relics':
		return to_color_green

	if msg_type == 'inactivity':
		return to_color_red

	return to_color_none

def colorize(msg, msg_type):

	color_func = get_color_func(msg_type)
	return color_func(msg)

class GuildTrackerThread(asyncio.Future):

	show_gear_pieces = False
	show_min_gear_level = 8
	show_min_level = 85
	show_min_stars = 5
	show_zetas = True
	show_omegas = True
	show_skills = False

	last_notify = {}

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
			messages.append(colorize(msg, 'nicks'))

		for base_id, new_unit in new_profile['roster'].items():

			unit_name = get_unit_name(base_id, lang)

			# Handle new units unlocked.

			if base_id not in old_roster:
				msg = '**%s** unlocked **%s**' % (new_player_name, unit_name)
				messages.append(colorize(msg, 'unlock-unit'))
				continue

			# Handle unit level increase.
			
			old_level = old_roster[base_id]['level']
			new_level = new_unit['level']
			if old_level < new_level and new_level >= self.show_min_level:
				msg = '**%s** promoted **%s** to level %d' % (new_player_name, unit_name, new_level)
				messages.append(colorize(msg, 'unit-level'))

			# Handle unit rarity increase.

			old_rarity = old_roster[base_id]['rarity']
			new_rarity = new_unit['rarity']
			if old_rarity < new_rarity and new_rarity >= self.show_min_stars:
				msg = '**%s** promoted **%s** to %d stars' % (new_player_name, unit_name, new_rarity)
				messages.append(colorize(msg, 'rarity'))

			# Handle gear level increase.

			old_gear_level = old_roster[base_id]['gear']
			new_gear_level = new_unit['gear']
			if old_gear_level < new_gear_level and new_gear_level >= self.show_min_gear_level:
				roman_gear = ROMAN[new_gear_level]
				msg = '**%s** increased **%s**\'s gear to level %s' % (new_player_name, unit_name, roman_gear)
				messages.append(colorize(msg, 'gear-level'))

			# Handle relic increase.

			old_relic = self.get_relic(old_roster[base_id])
			new_relic = self.get_relic(new_unit)
			if old_relic < new_relic:
				msg = '**%s** increased **%s** to relic %d' % (new_player_name, unit_name, new_relic)
				messages.append(colorize(msg, 'relics'))

			# TODO Handle when there was a gear level change because in that case we need to do things differently
			old_equipped = old_roster[base_id]['equipped']
			new_equipped = new_unit['equipped']
			diff_equipped = [ x for x in new_equipped if x not in old_equipped ]
			if diff_equipped:
				for gear in diff_equipped:
					gear_name = translate(gear['equipmentId'], lang)
					if self.show_gear_pieces:
						msg = '**%s** set **%s** on **%s**' % (new_player_name, gear_name, unit_name)
						messages.append(colorize(msg, 'gear-piece'))

			old_skills = { x['id']: x for x in old_roster[base_id]['skills'] }
			new_skills = { x['id']: x for x in new_unit['skills'] }

			for new_skill_id, new_skill in new_skills.items():

				skill_name = get_ability_name(new_skill_id, lang)

				if new_skill_id not in old_skills:
					msg = '**%s** unlocked new skill **%s** for **%s**' % (new_player_name, skill_name, unit_name)
					messages.append(colorize(msg, 'unlock-skill'))
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
							if unit_skill.is_zeta and self.show_zetas:
								msg = '**%s** applied Zeta upgrade **%s** (**%s**)' % (new_player_name, skill_name, unit_name)
								messages.append(colorize(msg, 'zetas'))

							elif self.show_omegas:
								msg = '**%s** applied Omega upgrade **%s** (**%s**)' % (new_player_name, skill_name, unit_name)
								messages.append(colorize(msg, 'omegas'))

						except BaseUnitSkill.DoesNotExist:
							print('ERROR: Could not find base unit skill with skill ID: %s' % new_skill_id)
					else:
						if self.show_skills:
							msg = '**%s** increased skill **%s** for **%s** to tier %d' % (new_player_name, skill_name, unit_name, new_skill['tier'])
							messages.append(colorize(msg, 'skill-increase'))

	def check_diff_player_level(self, old_profile, new_profile, messages):

		try:
			new_player_level = new_profile['profile']['level']
			old_player_level = old_profile['profile']['level']

			if old_player_level < new_player_level:
				msg = 'Player %s reached level %d' % (profile['profile']['name'], new_player_level)
				messages.append(colorize(msg, 'player-level'))

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
			messages.append(colorize(msg, 'inactivity'))

	def check_diff(self, old_profile, new_profile, messages):

		self.check_diff_player_level(old_profile, new_profile, messages)

		self.check_diff_player_units(old_profile, new_profile, messages)

		self.check_last_seen(new_profile, messages)

		return messages
		
	def update_player(self, ally_code, profile):

		if 'level' not in profile:
			print('ERROR: Problem with profile of %s' % ally_code)
			#print(json.dumps(profile, indent=4))
			return []

		roster = {}
		if 'roster' in profile:
			roster = { x['defId']: x for x in profile['roster'] }

		new_profile = {
			'profile': profile,
			'roster': roster,
		}

		if ally_code not in self.db:
			self.db[ally_code] = new_profile

		old_profile = self.db[ally_code]

		messages = self.check_diff(old_profile, new_profile, [])

		self.db[ally_code] = new_profile

		return messages

	async def run(self, guild_tracker):

		self.db = {}

		while True:

			session = await libswgoh.get_auth_guest()

			# TODO Retrieve guild mates in a dynamic way.
			guilds = [ my_guild ]
			for guild in guilds:

				messages = []
				members = guild['members']

				for member in members:

					ally_code = str(member)
					profile = await libswgoh.get_player_profile(ally_code=ally_code, session=session)

					messages = self.update_player(ally_code, profile)
					for message in messages:
						print(message)
						await guild_tracker.channel.send(message)

			print('end of pass')

			await asyncio.sleep(60)

class GuildTracker(discord.Client):

		channel = None

		async def on_ready(self):

			self.channel = self.get_channel(my_guild['channel_id'])

			print("Guild tracker bot ready!")
			if hasattr(self, 'initialized'):
				return

			setattr(self, 'initialized', True)

			print("Starting new thread.")
			self.loop.create_task(GuildTrackerThread().run(self))

config_file = 'config.json'
fin = open(config_file, 'r')
config = json.loads(fin.read())
fin.close()

if 'tokens' not in config:
	print('Key "tokens" missing from config %s' % config_file, file=sys.stderr)
	sys.exit(-1)

if 'arena-tracker' not in config['tokens']:
	print('Key "arena-tracker" missing from config %s' % config_file, file=sys.stderr)
	sys.exit(-1)


import logging
logging.basicConfig(level=logging.INFO)

GuildTracker().run(config['tokens']['arena-tracker'])
