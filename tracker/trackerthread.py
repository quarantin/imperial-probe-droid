#!/usr/bin/env python3

import re
import sys
import json
import redis
import asyncio
import discord
import libswgoh
import traceback
from discord.ext import commands
from discord import Forbidden, HTTPException, InvalidArgument, NotFound

from utils import translate
#from embed import new_embeds
from config import load_config
from constants import ROMAN, MAX_SKILL_TIER
from swgohhelp import get_unit_name, get_ability_name

import DJANGO
from swgoh.models import BaseUnitSkill, PremiumGuild, PremiumGuildConfig

class TrackerThread(asyncio.Future):

	def get_format(self, config, param):

		key = '%s.format' % param
		if key in config:
			return config[key]

		if param in PremiumGuildConfig.MESSAGE_FORMATS:
			return PremiumGuildConfig.MESSAGE_FORMATS[param]

	def get_channel(self, config, param):

		key = '%s.channel' % param
		if key in config:
			if config[key]:
				channel_id = self.bot.parse_opts_channel(config[key])
				return self.bot.get_channel(channel_id)

		key = 'default.channel'
		if key in config and config[key]:
			channel_id = self.bot.parse_opts_channel(config[key])
			return self.bot.get_channel(channel_id)

	def format_message(self, message, message_format):

		NONE   = lambda x: x
		ITALIC = lambda x: '_%s_' % x
		BOLD   = lambda x: '**%s**' % x
		ULINE  = lambda x: '__%s__' % x
		BOLD_ITALIC = lambda x: '***%s***' % x
		BOLD_ULINE = lambda x: '__**%s**__' % x

		subformats = {
			'': NONE,
			'gear.level': BOLD_ITALIC,
			'gear.level.roman': ITALIC,
			'gear.piece': BOLD_ITALIC,
			'last.seen': BOLD_ULINE,
			'level': BOLD_ULINE,
			'new.nick': BOLD,
			'nick': BOLD,
			'rarity': BOLD,
			'relic': BOLD,
			'skill': BOLD_ITALIC,
			'tier': BOLD,
			'unit': ULINE,
		}

		for key, value in message.items():
			fmt = key in subformats and subformats[key] or str
			message_format = message_format.replace('${%s}' % key, fmt(value))

		return message_format

	async def handle_arena_climbed_up(self, config, message):

		key = (message['type'] == 'char') and PremiumGuildConfig.MSG_SQUAD_ARENA_UP or PremiumGuildConfig.MSG_FLEET_ARENA_UP
		max_rank_key = (message['type'] == 'char') and PremiumGuildConfig.MSG_SQUAD_ARENA_RANK_MAX or PremiumGuildConfig.MSG_FLEET_ARENA_RANK_MAX
		if key in config and config[key] is False:
			return

		if max_rank_key in config and message['new.rank'] > config[max_rank_key]:
			return

		return key

	async def handle_arena_dropped_down(self, config, message):

		key = (message['type'] == 'char') and PremiumGuildConfig.MSG_SQUAD_ARENA_DOWN or PremiumGuildConfig.MSG_FLEET_ARENA_DOWN
		max_rank_key = (message['type'] == 'char') and PremiumGuildConfig.MSG_SQUAD_ARENA_RANK_MAX or PremiumGuildConfig.MSG_FLEET_ARENA_RANK_MAX
		if key in config and config[key] is False:
			return

		if max_rank_key in config and message['old.rank'] > config[max_rank_key]:
			return

		return key

	async def handle_gear_level(self, config, message):

		gear_level = message['gear.level']

		key = PremiumGuildConfig.MSG_UNIT_GEAR_LEVEL
		if key in config and config[key] is False:
			return

		min_key = PremiumGuildConfig.MSG_UNIT_GEAR_LEVEL_MIN
		if min_key in config and gear_level < config[min_key]:
			return

		return key

	async def handle_gear_piece(self, config, message):

		key = PremiumGuildConfig.MSG_UNIT_GEAR_PIECE
		if key in config and config[key] is False:
			return

		return key

	async def handle_inactivity(self, config, message):

		key = PremiumGuildConfig.MSG_INACTIVITY
		if key in config and config[key] is False:
			return

		return key

	async def handle_nick_change(self, config, message):

		key = PremiumGuildConfig.MSG_PLAYER_NICK
		if key in config and config[key] is False:
			return

		return key

	async def handle_player_level(self, config, message):

		level = message['level']

		key = PremiumGuildConfig.MSG_PLAYER_LEVEL
		if key in config and config[key] is False:
			return

		min_key = PremiumGuildConfig.MSG_PLAYER_LEVEL_MIN
		if min_key in config and level < config[min_key]:
			return

		return key

	async def handle_skill_unlocked(self, config, message):

		key = PremiumGuildConfig.MSG_UNIT_SKILL_UNLOCKED
		if key in config and config[key] is False:
			return

		return key

	async def handle_skill_increased(self, config, message):

		typ = message['type']
		tier = message['tier']

		if typ == 'omega':

			key = PremiumGuildConfig.MSG_UNIT_OMEGA
			if key in config and config[key] is False:
				return

		elif typ == 'zeta':

			key = PremiumGuildConfig.MSG_UNIT_ZETA
			if key in config and config[key] is False:
				return

		else:

			key = PremiumGuildConfig.MSG_UNIT_SKILL_INCREASED
			if key in config and config[key] is False:
				return

			min_key = PremiumGuildConfig.MSG_UNIT_SKILL_INCREASED_MIN
			if min_key in config and tier < config[min_key]:
				return

		return key

	async def handle_unit_level(self, config, message):

		level = message['level']

		key = PremiumGuildConfig.MSG_UNIT_LEVEL
		if key in config and config[key] is False:
			return

		min_key = PremiumGuildConfig.MSG_UNIT_LEVEL_MIN
		if min_key in config and level < config[min_key]:
			return

		return key

	async def handle_unit_rarity(self, config, message):

		rarity = message['rarity']

		key = PremiumGuildConfig.MSG_UNIT_RARITY
		if key in config and config[key] is False:
			return

		min_key = PremiumGuildConfig.MSG_UNIT_RARITY_MIN
		if min_key in config and rarity < config[min_key]:
			return

		return key

	async def handle_unit_relic(self, config, message):

		relic = message['relic']

		key = PremiumGuildConfig.MSG_UNIT_RELIC
		if key in config and config[key] is False:
			return

		min_key = PremiumGuildConfig.MSG_UNIT_RELIC_MIN
		if min_key in config and relic < config[min_key]:
			return

		return key

	async def handle_unit_unlocked(self, config, message):

		key = PremiumGuildConfig.MSG_UNIT_UNLOCKED
		if key in config and config[key] is False:
			return

		return key

	def prepare_message(self, config, message):

		if 'unit' in message:
			message['unit'] = get_unit_name(message['unit'], config['language'])

		if 'gear.level' in message:
			gear_level = message['gear.level']
			message['gear.level.roman'] = ROMAN[gear_level]

		if 'gear.piece' in message:
			message['gear.piece'] = translate(message['gear.piece'], config['language'])

		if 'skill' in message:
			message['skill.id'] = message['skill']
			message['skill'] = get_ability_name(message['skill'], config['language'])

		if 'tier' in message:

			message['type'] = ''
			if message['tier'] >= MAX_SKILL_TIER:
				try:
					skill = BaseUnitSkill.objects.get(skill_id=message['skill.id'])
					message['type'] = skill.is_zeta and 'zeta' or 'omega'

				except BaseUnitSkill.DoesNotExist:
					print('ERROR: Could not find base unit skill with id: %s' % message['skill.id'])

		return message

	async def run(self, bot):

		self.bot = bot
		self.config = bot.config
		self.redis = bot.config['redis']

		self.handlers = {

			PremiumGuildConfig.MSG_INACTIVITY:           self.handle_inactivity,
			PremiumGuildConfig.MSG_PLAYER_NICK:          self.handle_nick_change,
			PremiumGuildConfig.MSG_PLAYER_LEVEL:         self.handle_player_level,
			PremiumGuildConfig.MSG_UNIT_UNLOCKED:        self.handle_unit_unlocked,
			PremiumGuildConfig.MSG_UNIT_LEVEL:           self.handle_unit_level,
			PremiumGuildConfig.MSG_UNIT_RARITY:          self.handle_unit_rarity,
			PremiumGuildConfig.MSG_UNIT_RELIC:           self.handle_unit_relic,
			PremiumGuildConfig.MSG_UNIT_GEAR_LEVEL:      self.handle_gear_level,
			PremiumGuildConfig.MSG_UNIT_GEAR_PIECE:      self.handle_gear_piece,
			PremiumGuildConfig.MSG_UNIT_SKILL_UNLOCKED:  self.handle_skill_unlocked,
			PremiumGuildConfig.MSG_UNIT_SKILL_INCREASED: self.handle_skill_increased,
			PremiumGuildConfig.MSG_SQUAD_ARENA_UP:       self.handle_arena_climbed_up,
			PremiumGuildConfig.MSG_SQUAD_ARENA_DOWN:     self.handle_arena_dropped_down,
			PremiumGuildConfig.MSG_FLEET_ARENA_UP:       self.handle_arena_climbed_up,
			PremiumGuildConfig.MSG_FLEET_ARENA_DOWN:     self.handle_arena_dropped_down,
		}

		while True:

			self.guilds = list(PremiumGuild.objects.all())
			if not self.guilds:
				print('WARNING: No premium guild found.')

			for guild in self.guilds:

				ally_code = guild.ally_code
				config = guild.get_config()

				player_key = 'player|%s' % ally_code
				player = self.redis.get(player_key)
				if not player:
					print('ERROR: Could not find profile in redis: %s' % ally_code)
					continue

				player = json.loads(player.decode('utf-8'))
				if 'guildRefId' not in player:
					print('ERROR: Profile from redis is invalid: %s' % ally_code)
					continue

				messages_key = 'messages|%s' % player['guildRefId']
				count = self.redis.llen(messages_key)
				if count > 0 and guild.channel_id:
					messages = self.redis.lrange(messages_key, 0, count)

					for message in messages:

						message = json.loads(message)
						print(message)
						key = message['key']
						if key in self.handlers:
							key = await self.handlers[key](config, self.prepare_message(config, message))
							if key is not None:
								fmtstr = self.get_format(config, key)
								content = self.format_message(message, fmtstr)
								webhook_channel = self.get_channel(config, key)
								webhook_name = self.bot.get_webhook_name(key)
								webhook, error = await self.bot.get_webhook(webhook_name, webhook_channel)
								if error:
									try:
										await webhook_channel.send(error)
									except:
										pass
									return

								try:
									if not webhook:
										webhook, error = await self.bot.create_webhook(webhook_name, bot.get_avatar(), webhook_channel)
										if not webhook:
											print("create_webhook failed: %s" % error)
											await ctx.send(error)
										return

									await webhook.send(content=content, avatar_url=webhook.avatar_url)

								except InvalidArgument as err:
									print('ERROR: %s' % err)

								except NotFound as err:
									print('ERROR: %s' % err)

								except Forbidden as err:
									print('ERROR: %s' % err)

								except HTTPException as err:
									print('ERROR: %s' % err)

					ok = self.redis.ltrim(messages_key, count + 1, -1)
					if not ok:
						print('ERROR: redis.ltrim failed! Returned: %s' % ok)

			await asyncio.sleep(1)
