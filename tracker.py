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
from errors import error_invalid_config_key
from constants import ROMAN, MAX_SKILL_TIER
from swgohhelp import fetch_guilds, get_unit_name, get_ability_name

import DJANGO
from swgoh.models import BaseUnitSkill, Player, PremiumGuild, PremiumGuildConfig

def get_webhook_name(key):
	return 'IPD Tracker %s' % key

async def get_webhook(name, channel):

	try:
		webhooks = await channel.webhooks()
		for webhook in webhooks:
			if webhook.name.lower() == name.lower():
				return webhook, None

	except Forbidden:
		errmsg = 'I\'m not allowed to create webhooks in <#%s>.\nI need the following permission to proceed:\n- __**Manage Webhooks**__' % channel.id
		return None, errmsg

	except HTTPException:
		errmsg = 'I was not able to retrieve the webhook in <#%s> due to a network error.\nPlease try again.' % channel.id
		return None, errmsg

	return None, None

async def create_webhook(name, avatar, channel):

	perms = channel.permissions_for(channel.guild.me)
	if not perms.manage_webhooks:
		return [{
			'title': 'Permission Denied',
			'color': 'red',
			'description': 'I don\'t have permission to manage WebHooks in <#%s>.\nI need the following permission to proceed:\n- __**Manage Webhooks**__' % channel.id,
		}]

	try:
		webhook = await channel.create_webhook(name=name, avatar=avatar)
		return webhook, None

	except Forbidden:
		errmsg = 'I\'m not allowed to create webhooks in <#%s>.\nI need the following permission to proceed:\n- __**Manage Webhooks**__' % channel.id,
		return None, errmsg

	except HTTPException:
		errmsg = 'I was not able to create the webhook in <#%s> due to a network error.\nPlease try again.' % channel.id
		return None, errmsg

def parse_opts_channel(value):

	m = re.search(r'^<#([0-9]+)>$', value)
	if m:
		return int(m.group(1))

	return None

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
				return self.bot.get_channel(parse_opts_channel(config[key]))

		key = 'default.channel'
		if key in config and config[key]:
			return self.bot.get_channel(parse_opts_channel(config[key]))

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
		if key in config and config[key] is False:
			return

		return key

	async def handle_arena_dropped_down(self, config, message):

		key = (message['type'] == 'char') and PremiumGuildConfig.MSG_SQUAD_ARENA_DOWN or PremiumGuildConfig.MSG_FLEET_ARENA_DOWN
		if key in config and config[key] is False:
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

			key = PremiumGuildConfig.MSG_UNIT_SKILL_INCREASED_OMEGA
			if key in config and config[key] is False:
				return

		elif typ == 'zeta':

			key = PremiumGuildConfig.MSG_UNIT_SKILL_INCREASED_ZETA
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

		self.config = load_config()

		self.redis = self.config['redis']

		self.bot = bot

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
				messages_key = 'messages|%s' % player['guildRefId']
				count = self.redis.llen(messages_key)
				if count > 0:
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
								webhook_name = get_webhook_name(key)
								webhook, error = await get_webhook(webhook_name, webhook_channel)
								if error:
									try:
										await webhook_channel.send(error)
									except:
										pass
									return

								try:
									if not webhook:
										webhook, error = await create_webhook(webhook_name, bot.get_avatar(), webhook_channel)
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

class TrackerCog(commands.Cog):

	def __init__(self, bot, config):
		self.bot = bot
		self.config = config
		self.redis = config['redis']

	def parse_opts_boolean(self, value):

		lvalue = value.lower()

		if lvalue in [ 'on', 'true', 'enable', 'enabled' ]:
			return True

		if lvalue in [ 'off', 'false', 'disable', 'disabled' ]:
			return False

		return None

	def get_guild(self, author):

		try:
			player = Player.objects.get(discord_id=author.id)

		except Player.DoesNotExist:
			print('No player found')
			return None

		# Retrieve premium guild
		ally_code = str(player.ally_code)
		profile_key = 'player|%s' % player.ally_code
		profile = self.redis.get(profile_key)
		if not profile:
			print('Failed retrieving profile of %s' % player.ally_code)
			return None

		profile = json.loads(profile.decode('utf-8'))

		try:
			premium_guild = PremiumGuild.objects.get(guild_id=profile['guildRefId'])

		except PremiumGuild.DoesNotExist:
			print('No premium guild found')
			return None

		return premium_guild

	async def get_config(self, ctx, guild, pref_key=None):

		allow_all = pref_key is not None and pref_key in [ '*', 'all' ]

		output = ''
		for key, value in sorted(guild.get_config().items()):

			if (pref_key and pref_key not in key) and not allow_all:
				continue

			if key.endswith('.channel') and not allow_all:
				continue

			if key.endswith('.format') and not allow_all:
				continue

			if type(value) is int or key.endswith('.channel'):
				entry = '`%s` **%s**' % (key, value)

			elif type(value) is bool:
				boolval = value is True and 'On' or 'Off'
				entry = '`%s` **%s**' % (key, boolval)

			else:
				entry = '`%s` `"%s"`' % (key, value)

			entry += '\n'

			if len(output) + len(entry) > 2000:
				await ctx.send(output)
				output = ''

			output += entry

		await ctx.send(output)

	async def get_channels(self, ctx, guild, pref_key: str = None):

		output = ''
		channels = guild.get_channels()
		for key, channel in sorted(channels.items()):

			if pref_key is not None and pref_key not in key:
				continue

			key = key.replace('.channel', '')
			entry = '`%s` %s\n' % (key, channel)
			if len(output) + len(entry) > 2000:
				await ctx.send(output)
				output = ''

			output += entry

		await ctx.send(output)

	async def get_formats(self, ctx, guild, pref_key: str = None):

		output = ''
		formats = guild.get_formats()
		for key, fmt in sorted(formats.items()):

			if pref_key is not None and pref_key not in key:
				continue

			key = key.replace('.format', '')
			entry = '`%s` "%s"\n' % (key, fmt)
			if len(output) + len(entry) > 2000:
				await ctx.send(outut)
				output = ''

			output += entry

		await ctx.send(output)

	async def set_config(self, ctx, guild, pref_key: str, pref_value: str):

		config = guild.get_config()

		if pref_key not in config:
			message = error_invalid_config_key(self.bot.command_prefix, pref_key)
			await ctx.send(message)
			return

		try:
			entry = PremiumGuildConfig.objects.get(guild=guild, key=pref_key)

		except PremiumGuildConfig.DoesNotExist:
			entry = PremiumGuildConfig(guild=guild, key=pref_key)

		boolval = self.parse_opts_boolean(pref_value)

		if pref_key.endswith('.channel'):
			entry.value = parse_opts_channel(pref_value)
			entry.value_type = 'chan'

		if pref_key.endswith('.format'):
			entry.value = pref_value
			entry.value_type = 'fmt'

		elif pref_key.endswith('.min') or pref_key.endswith('.repeat'):
			entry.value = int(pref_value)
			entry.value_type = int.__name__

		elif boolval is not None:
			entry.value = boolval
			entry.value_type = bool.__name__

		else:
			entry.value = pref_value
			entry.value_type = str.__name__

		entry.save()

		display_value = entry.value

		if entry.value_type == 'bool':
			display_value = display_value is True and '`On`' or '`Off`'

		elif entry.value_type == 'chan':
			display_value = '<#%s>' % display_value

		message = 'The following setting has been saved:\n`%s` = %s' % (pref_key, display_value)
		await ctx.send(message)

	async def set_channels(self, ctx, guild, pref_key: str, pref_value: str):

		config = guild.get_config()

		if not pref_key.endswith('.channel'):
			if pref_key != 'default' and pref_key not in PremiumGuildConfig.MESSAGE_FORMATS:
				message = error_invalid_config_key(self.bot.command_prefix, pref_key)
				await ctx.send(message)
				return

			pref_key = '%s.channel' % pref_key

		if pref_key not in config:
			message = error_invalid_config_key(self.bot.command_prefix, pref_key)
			await ctx.send(message)
			return

		channel_id = parse_opts_channel(pref_value)
		webhook_channel = self.bot.get_channel(channel_id)
		webhook_name = get_webhook_name(pref_key.replace('.channel', ''))
		webhook, error = await get_webhook(webhook_name, webhook_channel)
		if not webhook:
			if error:
				print("WTF: %s %s" % (type(error), error))
				await ctx.send(error)
				return

			webhook, error = await create_webhook(webhook_name, self.bot.get_avatar(), webhook_channel)
			if not webhook:
				print("create_webhook failed: %s" % error)
				await ctx.send(error)
				return

		try:
			entry = PremiumGuildConfig.objects.get(guild=guild, key=pref_key)

		except PremiumGuildConfig.DoesNotExist:
			entry = PremiumGuildConfig(guild=guild, key=pref_key)

		entry.value = channel_id
		entry.value_type = 'chan'
		entry.save()

		message = 'The following channel has been saved:\n`%s` = %s' % (pref_key, pref_value)
		await ctx.send(message)

	async def set_formats(self, ctx, guild, pref_key: str, pref_value: str):

		config = guild.get_config()

		if not pref_key.endswith('.format'):
			if pref_key not in PremiumGuildConfig.MESSAGE_FORMATS:
				message = error_invalid_config_key(self.bot.command_prefix, pref_key)
				await ctx.send(message)
				return

			pref_key = '%s.format' % pref_key

		if pref_key not in config:
			message = error_invalid_config_key(self.bot.command_prefix, pref_key)
			await ctx.send(message)
			return

		try:
			entry = PremiumGuildConfig.objects.get(guild=guild, key=pref_key)

		except PremiumGuildConfig.DoesNotExist:
			entry = PremiumGuildConfig(guild=guild, key=pref_key)

		entry.value = pref_value
		entry.value_type = 'fmt'
		entry.save()

		message = 'The following format has been saved:\n`%s` = "%s"' % (pref_key, pref_value)
		await ctx.send(message)

	@commands.group()
	async def tracker(self, ctx):
		if ctx.invoked_subcommand is None:
			print('HELP')

	@tracker.command()
	async def config(self, ctx, pref_key: str = None, pref_value: str = None):

		guild = self.get_guild(ctx.author)

		if pref_key and pref_value:
			return await self.set_config(ctx, guild, pref_key, pref_value)

		return await self.get_config(ctx, guild, pref_key)

	@tracker.command()
	async def channels(self, ctx, pref_key: str = None, pref_value: str = None):

		guild = self.get_guild(ctx.author)

		if pref_key and pref_value:
			return await self.set_channels(ctx, guild, pref_key, pref_value)

		return await self.get_channels(ctx, guild, pref_key)

	@tracker.command()
	async def formats(self, ctx, pref_key: str = None, pref_value: str = None):

		guild = self.get_guild(ctx.author)

		if pref_key and pref_value:
			return await self.set_formats(ctx, guild, pref_key, pref_value)

		return await self.get_formats(ctx, guild, pref_key)

class Tracker(commands.Bot):

	def get_avatar(self):
		with open('images/imperial-probe-droid.jpg', 'rb') as image:
			return bytearray(image.read())

	async def on_ready(self):

		attr = 'initialized'
		if not hasattr(self, attr):

			setattr(self, attr, True)

			self.add_cog(TrackerCog(self, load_config()))

			print('Starting tracker thread.')
			self.loop.create_task(TrackerThread().run(self))

		msg = 'Tracker bot ready!'
		print(msg)
		await self.get_channel(575654803099746325).send(msg)

if __name__ == '__main__':

	from config import load_config, setup_logs

	setup_logs('discord', 'logs/tracker-discord.log')

	config = load_config()

	if 'tokens' not in config:
		print('Key "tokens" missing from config', file=sys.stderr)
		sys.exit(-1)

	if 'tracker' not in config['tokens']:
		print('Key "tracker" missing from config', file=sys.stderr)
		sys.exit(-1)

	try:
		Tracker(command_prefix=config['prefix']).run(config['tokens']['tracker'])

	except:
		print(traceback.format_exc())
