#!/usr/bin/env python3

import re
import sys
import json
import asyncio
import traceback
from discord.ext import commands
from discord import Forbidden, HTTPException, InvalidArgument, NotFound

from utils import translate
from embed import new_embeds
from config import load_config
from constants import ROMAN, MAX_SKILL_TIER
from swgohhelp import get_unit_name, get_ability_name

import DJANGO
from swgoh.models import BaseUnitSkill, Player, PremiumGuild

class TrackerThread(asyncio.Future):

	def get_channel(self, config, param):

		key = '%s.channel' % param
		if key in config and config[key]:
			channel_id = self.bot.parse_opts_channel(config[key])
			return self.bot.get_channel(channel_id)

		key = 'default.channel'
		if key in config and config[key]:
			channel_id = self.bot.parse_opts_channel(config[key])
			return self.bot.get_channel(channel_id)

	async def handle_arena_climbed_up(config, message):

		key = (message['type'] == 'char') and PremiumGuild.MSG_ARENA_RANK_UP or PremiumGuild.MSG_FLEET_RANK_UP
		max_rank_key = (message['type'] == 'char') and PremiumGuild.MSG_ARENA_RANK_MAX or PremiumGuild.MSG_FLEET_RANK_MAX
		if key in config and config[key] is False:
			return

		if max_rank_key in config and message['new.rank'] > config[max_rank_key]:
			return

		return key

	async def handle_arena_dropped_down(config, message):

		key = (message['type'] == 'char') and PremiumGuild.MSG_ARENA_RANK_DOWN or PremiumGuild.MSG_FLEET_RANK_DOWN
		max_rank_key = (message['type'] == 'char') and PremiumGuild.MSG_ARENA_RANK_MAX or PremiumGuild.MSG_FLEET_RANK_MAX
		if key in config and config[key] is False:
			return

		if max_rank_key in config and message['old.rank'] > config[max_rank_key]:
			return

		return key

	async def handle_gear_level(config, message):

		gear_level = message['gear.level']

		key = PremiumGuild.MSG_UNIT_GEAR_LEVEL
		if key in config and config[key] is False:
			return

		min_key = PremiumGuild.MSG_UNIT_GEAR_LEVEL_MIN
		if min_key in config and gear_level < config[min_key]:
			return

		return key

	async def handle_gear_piece(config, message):

		key = PremiumGuild.MSG_UNIT_GEAR_PIECE
		if key in config and config[key] is False:
			return

		return key

	async def handle_inactivity(config, message):

		key = PremiumGuild.MSG_INACTIVITY
		if key in config and config[key] is False:
			return

		return key

	async def handle_nick_change(config, message):

		key = PremiumGuild.MSG_PLAYER_NICK
		if key in config and config[key] is False:
			return

		return key

	async def handle_player_level(config, message):

		level = message['level']

		key = PremiumGuild.MSG_PLAYER_LEVEL
		if key in config and config[key] is False:
			return

		min_key = PremiumGuild.MSG_PLAYER_LEVEL_MIN
		if min_key in config and level < config[min_key]:
			return

		return key

	async def handle_skill_unlocked(config, message):

		key = PremiumGuild.MSG_UNIT_SKILL_UNLOCKED
		if key in config and config[key] is False:
			return

		return key

	async def handle_skill_increased(config, message):

		typ = message['type']
		tier = message['tier']

		if typ == 'omega':

			key = PremiumGuild.MSG_UNIT_OMEGA
			if key in config and config[key] is False:
				return

		elif typ == 'zeta':

			key = PremiumGuild.MSG_UNIT_ZETA
			if key in config and config[key] is False:
				return

		else:

			key = PremiumGuild.MSG_UNIT_SKILL_INCREASED
			if key in config and config[key] is False:
				return

			min_key = PremiumGuild.MSG_UNIT_SKILL_INCREASED_MIN
			if min_key in config and tier < config[min_key]:
				return

		return key

	async def handle_unit_level(config, message):

		level = message['level']

		key = PremiumGuild.MSG_UNIT_LEVEL
		if key in config and config[key] is False:
			return

		min_key = PremiumGuild.MSG_UNIT_LEVEL_MIN
		if min_key in config and level < config[min_key]:
			return

		return key

	async def handle_unit_rarity(config, message):

		rarity = message['rarity']

		key = PremiumGuild.MSG_UNIT_RARITY
		if key in config and config[key] is False:
			return

		min_key = PremiumGuild.MSG_UNIT_RARITY_MIN
		if min_key in config and rarity < config[min_key]:
			return

		return key

	async def handle_unit_relic(config, message):

		relic = message['relic']

		key = PremiumGuild.MSG_UNIT_RELIC
		if key in config and config[key] is False:
			return

		min_key = PremiumGuild.MSG_UNIT_RELIC_MIN
		if min_key in config and relic < config[min_key]:
			return

		return key

	async def handle_unit_unlocked(config, message):

		key = PremiumGuild.MSG_UNIT_UNLOCKED
		if key in config and config[key] is False:
			return

		return key

	def prepare_nick(self, ally_code):

		try:
			players = Player.objects.filter(ally_code=ally_code)
			for player in players:
				if player.discord_id:
					return '<@!%s>' % player.discord_id

		except Player.DoesNotExist:
			pass

		self.logger.info('prepare_nick: Could not find player with allycode: %s' % ally_code)
		return None

	def prepare_message(self, config, message):

		if 'key' in message and 'nick' in message and 'ally.code' in message:
			prep_key = '%s.%s.mention' % (message['key'], message['ally.code'])
			if prep_key in config and config[prep_key] is not False:
				prep_nick = self.prepare_nick(message['ally.code'])
				if prep_nick:
					message['nick'] = prep_nick

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
					self.logger.error('Could not find base unit skill with id: %s' % message['skill.id'])

		return message

	handlers = {

		PremiumGuild.MSG_INACTIVITY:           handle_inactivity,
		PremiumGuild.MSG_PLAYER_NICK:          handle_nick_change,
		PremiumGuild.MSG_PLAYER_LEVEL:         handle_player_level,
		PremiumGuild.MSG_UNIT_UNLOCKED:        handle_unit_unlocked,
		PremiumGuild.MSG_UNIT_LEVEL:           handle_unit_level,
		PremiumGuild.MSG_UNIT_RARITY:          handle_unit_rarity,
		PremiumGuild.MSG_UNIT_RELIC:           handle_unit_relic,
		PremiumGuild.MSG_UNIT_GEAR_LEVEL:      handle_gear_level,
		PremiumGuild.MSG_UNIT_GEAR_PIECE:      handle_gear_piece,
		PremiumGuild.MSG_UNIT_SKILL_UNLOCKED:  handle_skill_unlocked,
		PremiumGuild.MSG_UNIT_SKILL_INCREASED: handle_skill_increased,
		PremiumGuild.MSG_ARENA_RANK_UP:        handle_arena_climbed_up,
		PremiumGuild.MSG_ARENA_RANK_DOWN:      handle_arena_dropped_down,
		PremiumGuild.MSG_FLEET_RANK_UP:        handle_arena_climbed_up,
		PremiumGuild.MSG_FLEET_RANK_DOWN:      handle_arena_dropped_down,
	}

	async def dump_messages(self, guild_ref_id, guild, config):

		if not guild.channel_id:
			return

		messages_key = 'messages|%s' % guild_ref_id
		count = self.redis.llen(messages_key)
		if not count:
			return

		while True:

			messages = self.redis.lrange(messages_key, 0, 0)
			if not messages:
				break

			message = json.loads(messages[0].decode('utf-8'))
			self.logger.info(message)
			key = message['key']
			if key in self.handlers:
				prep_message = self.prepare_message(config, message)
				key = await self.handlers[key](config, prep_message)
				if key is not None:
					fmtstr = self.bot.get_format(config, key)
					content = self.bot.format_message(message, fmtstr)
					webhook_channel = self.get_channel(config, key)
					webhook_name = self.bot.get_webhook_name()
					webhook, error = await self.bot.get_webhook(webhook_name, webhook_channel)
					if error:
						self.logger.error(error)
						return

					try:
						if not webhook:
							webhook, error = await self.bot.create_webhook(webhook_name, self.bot.get_avatar(), webhook_channel)
							if not webhook or error:
								errmsg = 'self.bot.create_webhook failed: %s' % error
								self.logger.error(errmsg)
							return

						if type(content) is str:
							await webhook.send(content=content, avatar_url=webhook.avatar_url)

						elif type(content) is dict:
							embeds = new_embeds(content, add_sep=False, footer=False)
							for embed in embeds:
								await webhook.send(content='', embed=embed, avatar_url=webhook.avatar_url)

						else:
							raise Exception('This should never happen!')

					except InvalidArgument as err:
						self.logger.error(str(err))

					except NotFound as err:
						self.logger.error(str(err))

					except Forbidden as err:
						self.logger.error(str(err))

					except HTTPException as err:
						self.logger.error(str(err))

			self.redis.lpop(messages_key)

	async def run(self, bot):

		self.bot = bot
		self.config = bot.config
		self.logger = bot.logger
		self.redis = bot.redis

		while True:

			self.guilds = list(PremiumGuild.objects.all())
			if not self.guilds:
				self.logger.warning('No premium guild found')

			for guild in self.guilds:

				ally_code = guild.ally_code
				config = guild.get_config()

				player_key = 'player|%s' % ally_code
				player = self.redis.get(player_key)
				if not player:
					self.logger.error('Could not find profile in redis: %s' % ally_code)
					continue

				player = json.loads(player.decode('utf-8'))
				if 'guildRefId' not in player:
					self.logger.error('Profile from redis is invalid: %s' % ally_code)
					continue

				await self.dump_messages(player['guildRefId'], guild, config)

			await asyncio.sleep(1)
