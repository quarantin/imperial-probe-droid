#!/usr/bin/env python3

import sys
import json
import redis
import asyncio
import discord
import libswgoh
import traceback

import DJANGO
from swgoh.models import BaseUnitSkill, PremiumGuild

from utils import translate
from constants import ROMAN, MAX_SKILL_TIER
from swgohhelp import get_unit_name, get_ability_name

LAST_SEEN_MAX_HOURS = 48
LAST_SEEN_MAX_HOURS_INTERVAL = 24

class GuildConfig:

	language = 'eng_us'
	show_gear_level = True
	show_gear_level_min = 0 # 8
	show_gear_piece = True
	show_inactivity = True
	show_inactivity_min = 48
	show_inactivity_repeat = 24
	show_nick_change = True
	show_player_level = True
	show_player_level_min = 0
	show_relic = True
	show_relic_min = 0
	show_skill_unlocked = True
	show_skill_increased = True
	show_skill_increased_min = 0 # MAX_SKILL_TIER
	show_skill_increased_omega = True
	show_skill_increased_zeta = True
	show_unit_level = True
	show_unit_level_min = 0 # 85
	show_unit_rarity = True
	show_unit_rarity_min = 0
	show_unit_unlocked = True

class GuildTrackerThread(asyncio.Future):

	bot = None

	async def send_msg(self, channel, message):

		try:
			print(message)
			await channel.send(message)

		except:
			print('Failed sending to channel #%s (%s)' % (channel, channel.id))
			print(traceback.format_exc())

	async def handle_gear_level(self, config, message):

		if config.show_gear_level is False:
			return

		gear_level = message['gear-level']
		if gear_level < config.show_gear_level_min:
			return

		roman_gear = ROMAN[gear_level]
		msg = '**%s** increased **%s**\'s gear to level **%s**' % (message['nick'], message['unit'], roman_gear)
		await self.send_msg(config.channel, msg)

	async def handle_gear_piece(self, config, message):

		if config.show_gear_piece is False:
			return

		gear_piece = message['gear-piece']
		msg = '**%s** set **%s** on **%s**' % (message['nick'], gear_piece, message['unit'])
		await self.send_msg(config.channel, msg)

	async def handle_inactivity(self, config, message):

		if config.show_inactivity is False:
			return

		msg = '**%s** has been inactive for **%s**' % (message['nick'], message['last_seen'])
		await self.send_msg(config.channel, msg)

	async def handle_nick_change(self, config, message):

		if config.show_nick_change is False:
			return

		msg = '**%s** is now known as **%s**' % (message['nick'], message['new_nick'])
		await self.send_msg(config.channel, msg)

	async def handle_player_level(self, config, message):

		if config.show_player_level is False:
			return

		if message['level'] < config.show_player_level_min:
			return

		msg = '**%s** reached level **%s**' % (message['nick'], message['level'])
		await self.send_msg(config.channel, msg)

	async def handle_skill_unlocked(self, config, message):

		if config.show_skill_unlocked is False:
			return

		msg = '**%s** unlocked **%s**\'s new skill **%s**' % (message['nick'], message['unit'], message['skill'])
		await self.send_msg(config.channel, msg)

	async def handle_skill_increased(self, config, message):

		if config.show_skill_increased is False:
			return

		if message['tier'] < config.show_skill_increased_min:
			return

		if message['type'] == 'omega':
			msg = '**%s** applied **Omega** to **%s**\'s skill **%s**' % (message['nick'], message['unit'], message['skill'])

		elif message['type'] == 'zeta':
			msg = '**%s** applied **Zeta** to **%s**\'s skill **%s**' % (message['nick'], message['unit'], message['skill'])

		else:
			msg = '**%s** increased **%s**\'s skill **%s** to tier **%s**' % (message['nick'], message['unit'], message['skill'], message['tier'])

		await self.send_msg(config.channel, msg)

	async def handle_unit_level(self, config, message):

		if config.show_unit_level is False:
			return

		if message['level'] < config.show_unit_level_min:
			return

		msg = '**%s** increased **%s**\'s to level **%s**' % (message['nick'], message['unit'], message['level'])
		await self.send_msg(config.channel, msg)

	async def handle_unit_rarity(self, config, message):

		if config.show_unit_rarity is False:
			return

		if message['rarity'] < config.show_unit_rarity_min:
			return

		msg = '**%s** promoted **%s** to **%s** stars' % (message['nick'], message['unit'], message['rarity'])
		await self.send_msg(config.channel, msg)

	async def handle_unit_relic(self, config, message):

		if config.show_relic is False:
			return

		if message['relic'] < config.show_relic_min:
			return

		msg = '**%s** increased **%s** to relic **%s**' % (message['nick'], message['unit'], message['relic'])
		await self.send_msg(config.channel, msg)

	async def handle_unit_unlocked(self, config, message):

		if config.show_unit_unlocked is False:
			return

		msg = '**%s** unlocked **%s**' % (message['nick'], message['unit'])
		await self.send_msg(config.channel, msg)

	def prepare_message(self, config, message):

		if 'unit' in message:
			message['unit'] = get_unit_name(message['unit'], config.language)

		if 'gear-piece' in message:
			message['gear-piece'] = translate(message['gear-piece'], config.language)

		if 'skill' in message:
			message['skill-id'] = message['skill']
			message['skill'] = get_ability_name(message['skill'], config.language)

		if 'tier' in message:

			message['type'] = ''
			if message['tier'] >= MAX_SKILL_TIER:
				try:
					skill = BaseUnitSkill.objects.get(skill_id=message['skill-id'])
					message['type'] = skill.is_zeta and 'zeta' or 'omega'

				except BaseUnitSkill.DoesNotExist:
					print('ERROR: Could not find base unit skill with id: %s' % message['skill-id'])

		return message

	async def run(self, bot):

		from config import load_config
		config = load_config()

		self.bot = bot
		self.redis = redis.Redis()

		self.mapping = {
			'gear level': self.handle_gear_level,
			'gear piece': self.handle_gear_piece,
			'inactivity': self.handle_inactivity,
			'nick change': self.handle_nick_change,
			'player level': self.handle_player_level,
			'skill unlocked': self.handle_skill_unlocked,
			'skill increased': self.handle_skill_increased,
			'unit level': self.handle_unit_level,
			'unit rarity': self.handle_unit_rarity,
			'unit relic': self.handle_unit_relic,
			'unit unlocked': self.handle_unit_unlocked,
		}

		while True:

			self.guilds = list(PremiumGuild.objects.all())
			for guild in self.guilds:

				ally_code = guild.ally_code
				gconfig = GuildConfig()
				gconfig.channel = self.bot.get_channel(guild.channel_id)

				player_key = 'player|%s' % ally_code
				player = config['redis'].get(player_key)
				if not player:
					print('ERROR: Could not find profile in redis: %s' % ally_code)
					continue

				player = json.loads(player.decode('utf-8'))
				messages_key = 'messages|%s' % player['guildRefId']
				count = self.redis.llen(messages_key)
				if count > 0:
					messages = self.redis.lrange(messages_key, 0, count)

					for message in messages:

						message = json.loads(message)
						print(message)
						tag = message['tag']
						if tag in self.mapping:
							await self.mapping[tag](gconfig, self.prepare_message(gconfig, message))

					ok = self.redis.ltrim(messages_key, count + 1, -1)
					if not ok:
						print('redis.ltrim failed! Returned: %s' % ok)


			await asyncio.sleep(1)

class GuildTracker(discord.Client):

	async def on_ready(self):

		if not hasattr(self, 'initialized'):

			setattr(self, 'initialized', True)

			print('Starting new thread')
			self.loop.create_task(GuildTrackerThread().run(self))

		print('Guild tracker bot ready!')
		await self.get_channel(575654803099746325,).send('Guild tracker bot ready!')

if __name__ == '__main__':

	config_file = 'config.json'
	fin = open(config_file, 'r')
	config = json.loads(fin.read())
	fin.close()

	if 'tokens' not in config:
		print('Key "tokens" missing from config %s' % config_file, file=sys.stderr)
		sys.exit(-1)

	if 'tracker' not in config['tokens']:
		print('Key "tracker" missing from config %s' % config_file, file=sys.stderr)
		sys.exit(-1)


	import logging
	logging.basicConfig(level=logging.INFO)

	try:
		GuildTracker().run(config['tokens']['tracker'])
	except:
		print(traceback.format_exc())
