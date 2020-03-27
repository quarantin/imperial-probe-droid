#!/usr/bin/env python3

import json
import discord
from discord.ext import commands

from constants import EMOJIS
from errors import error_invalid_config_key, error_invalid_config_value, error_no_ally_code_specified

import DJANGO
from swgoh.models import Player, PremiumGuild, PremiumGuildConfig

CONFIG_MAX_KEY_LEN = 19
CHANNELS_MAX_KEY_LEN = 15
FORMATS_MAX_KEY_LEN = 15
MENTIONS_MAX_KEY_LEN = 15

class TrackerCog(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.config = bot.config
		self.logger = bot.logger
		self.redis = bot.redis

	def get_allycode_by_discord_id(self, discord_id):

		try:
			player = Player.objects.get(discord_id=discord_id)
			return player.ally_code

		except Player.DoesNotExist:
			pass

		return None

	def get_guild(self, author):

		try:
			player = Player.objects.get(discord_id=author.id)

		except Player.DoesNotExist:
			self.logger.warning('TrackerCog.get_guild(%s): No player found' % author.id)
			return None

		ally_code = str(player.ally_code)
		profile_key = 'player|%s' % player.ally_code
		profile = self.redis.get(profile_key)
		if not profile:
			self.logger.warning('Failed retrieving profile of %s' % player.ally_code)
			return None

		profile = json.loads(profile.decode('utf-8'))

		try:
			premium_guild = PremiumGuild.objects.get(guild_id=profile['guildRefId'])

		except PremiumGuild.DoesNotExist:
			self.logger.warning('No premium guild found for ID: %s' % profile['guildRefId'])
			return None

		return premium_guild

	def get_matching_keys(self, ctx, guild, pref_key, config=False, channels=False, formats=False, mentions=False):

		keys = []
		for key, value in sorted(guild.get_config(discord_id=ctx.author.id).items()):

			add = False
			if config is True and key.endswith('.config'):
				add = True

			elif channels is True and key.endswith('.channel'):
				add = True

			elif formats is True and key.endswith('.format'):
				add = True

			elif mentions is True and key.endswith('.mention'):
				add = True

			if add and (pref_key.lower() in key or pref_key.lower() == 'all'):
				keys.append(key)

		return keys

	def pad(self, string, length):
		pad_len = length - len(string)
		return string + ('\u00a0' * pad_len)

	def get_header(self, count=3):

		emo = EMOJIS['']

		extra3 = (count == 3 and ' ' or '')
		extra2 = (count == 2 and emo or '')
		spacer = ' '.join([ emo ] * count)

		header = '`|`%s%s**Key**%s%s%s`|` **Value**\n' % (spacer, extra3, extra3, extra2, spacer)

		return header

	get_config_help = """
To update configuration, just type:
```
%prefixtracker config <key> <value>```
For example to disable `arena.rank.up` events, just type:
```
%prefixtracker config arena.rank.up off```"""

	async def get_config(self, ctx, guild, pref_key=None):

		lines = []
		config = guild.get_config()
		for key, value in sorted(config.items()):

			if pref_key is not None and pref_key not in key:
				continue

			if not key.endswith('.config'):
				continue

			key = key.replace('.config', '')
			padded_key = self.pad(key, CONFIG_MAX_KEY_LEN)
			if type(value) is bool:
				boolval = value is True and 'ON' or 'OFF'
				lines.append('`|%s|` **%s**' % (padded_key, boolval))

			else:
				lines.append('`|%s|` **%s**' % (padded_key, value))

		if not lines:
			description = 'No matching keys for: `%s`' % pref_key

		else:
			sep = self.bot.config['separator']
			prefix = self.bot.command_prefix
			cmdhelp = self.get_config_help.replace('%prefix', prefix)
			description = self.get_header(count=3) + sep + '\n' + '\n'.join(lines) + '\n' + sep + '\n' + cmdhelp

		embed = discord.Embed(title='Tracker Configuration', description=description)
		await ctx.send(embed=embed)

	get_channels_help = """
To update channels, just type:
```
%prefixtracker channels <key> <channel>```
For example to redirect `arena.rank.down` events to **#arena-tracker** channel, just type:
```
%prefixtracker channels arena.rank.up #arena-tracker```"""

	async def get_channels(self, ctx, guild, pref_key: str = None):

		lines = []
		channels = guild.get_channels()
		for key, channel in sorted(channels.items()):

			if pref_key is not None and pref_key not in key:
				continue

			key = key.replace('.channel', '')
			padded_key = self.pad(key, CHANNELS_MAX_KEY_LEN)
			lines.append('`|%s|` %s' % (padded_key, channel))

		if not lines:
			description = 'No matching keys for: `%s`' % pref_key

		else:
			sep = self.bot.config['separator']
			prefix = self.bot.command_prefix
			cmdhelp = self.get_channels_help.replace('%prefix', prefix)
			description = self.get_header(count=2) + sep + '\n' + '\n'.join(lines) + '\n' + sep + '\n' + cmdhelp

		embed = discord.Embed(title='Channels Configuration', description=description)
		await ctx.send(embed=embed)

	get_formats_help = """
To update formats, just type:
```
%prefixtracker formats <key> <format>```
For example to configure formats for `arena.rank.down` events, just type:
```
%prefixtracker formats arena.rank.down "**${nick}** has _dropped down_ in **squad** arena: __**${old.rank} => ${new.rank}**__"```"""

	async def get_formats(self, ctx, guild, pref_key: str = None):

		lines = []
		formats = guild.get_formats()
		for key, fmt in sorted(formats.items()):

			if pref_key is not None and pref_key not in key:
				continue

			key = key.replace('.format', '')
			padded_key = self.pad(key, FORMATS_MAX_KEY_LEN)
			lines.append('`|%s|` "%s"' % (padded_key, fmt))

		if not lines:
			description = 'No matching keys for: `%s`' % pref_key

		else:
			sep = self.bot.config['separator']
			prefix = self.bot.command_prefix
			cmdhelp = self.get_formats_help.replace('%prefix', prefix)
			description = self.get_header(count=2) + sep + '\n' + '\n'.join(lines) + '\n' + sep + '\n' + cmdhelp

		embed = discord.Embed(title='Formats Configuration', description=description)
		await ctx.send(embed=embed)

	get_mentions_help = """
To update mentions, just type:
```
%prefixtracker mentions <key> <value>```
For example to enable notifications for `arena.rank.down` events, just type:
```
%prefixtracker mentions arena.rank.down on```"""

	async def get_mentions(self, ctx, guild, pref_key: str = None):

		ally_code = self.get_allycode_by_discord_id(ctx.author.id)
		if not ally_code:
			errors = error_no_ally_code_specified(self.config, ctx.author)
			await ctx.send(errors[0]['description'])
			return

		lines = []
		mentions = guild.get_mentions(ally_code=ally_code)
		for key, mention in sorted(mentions.items()):

			if pref_key is not None and pref_key not in key:
				continue

			to_replace = '.%s.mention' % ally_code
			key = key.replace(to_replace, '')
			padded_key = self.pad(key, MENTIONS_MAX_KEY_LEN)

			if type(mention) is str and mention.isnumeric():
				mention = int(mention)

			if type(mention) is bool:
				mention = '**%s**' % (mention is True and 'ON' or 'OFF')

			elif type(mention) is int:
				mention = int(mention)
				mention = '<@!%s>' % mention

			else:
				raise Exception('Unsupported operand: %s (%s)' % (mention, type(mention)))

			lines.append('`|%s|` %s' % (padded_key, mention))


		if not lines:
			description = 'No matching keys for: `%s`' % pref_key

		else:
			sep = self.bot.config['separator']
			prefix = self.bot.command_prefix
			cmdhelp = self.get_mentions_help.replace('%prefix', prefix)
			description = self.get_header(count=2) + sep + '\n' + '\n'.join(lines) + '\n' + sep + '\n' + cmdhelp

		embed = discord.Embed(title='Mentions Configuration', description=description)
		await ctx.send(embed=embed)

	async def set_config(self, ctx, guild, pref_key: str, pref_value: str):

		pref_keys = self.get_matching_keys(ctx, guild, pref_key, config=True)
		if not pref_keys:
			message = error_invalid_config_key('config', self.bot.command_prefix, pref_key)
			await ctx.send(message)
			return

		if len(pref_keys) > 1:
			pref_keys = [ '`%s`' % x for x in pref_keys if x.endswith('.config') ]
			message = '__**%s**__ matches more than one entry:\n%s' % (pref_key, '\n'.join(pref_keys))
			await ctx.send(message)
			return

		lines = []
		for pref_key in pref_keys:

			try:
				entry = PremiumGuildConfig.objects.get(guild=guild, key=pref_key)

			except PremiumGuildConfig.DoesNotExist:
				entry = PremiumGuildConfig(guild=guild, key=pref_key)

			boolval = self.bot.parse_opts_boolean(pref_value)

			display_value = entry.value

			if pref_key.endswith('.min') or pref_key.endswith('.repeat'):
				entry.value = int(pref_value)
				entry.value_type = int.__name__

			elif boolval is not None:
				entry.value = boolval
				entry.value_type = 'bool'
				display_value = boolval is True and '**ON**' or '**OFF**'

			else:
				entry.value = pref_value
				entry.value_type = 'str'

			entry.save()

			lines.append('`%s` %s' % (pref_key, display_value))

		if lines:
			plural = len(lines) > 1 and 's' or ''
			plural_have = len(lines) > 1 and 'have' or 'has'
			lines.insert(0, 'The following setting%s %s been saved:' % (plural, plural_have))
			await ctx.send('\n'.join(lines))

	async def set_channels(self, ctx, guild, pref_key: str, pref_value: str):

		pref_keys = self.get_matching_keys(ctx, guild, pref_key, channels=True)
		if not pref_keys:
			message = error_invalid_config_key('channels', self.bot.command_prefix, pref_key)
			await ctx.send(message)
			return

		lines = []
		for pref_key in pref_keys:

			if not pref_key.endswith('.channel'):
				if pref_key != 'default' and pref_key not in PremiumGuild.MESSAGE_FORMATS:
					message = error_invalid_config_key('channels', self.bot.command_prefix, pref_key)
					await ctx.send(message)
					return

				pref_key = '%s.channel' % pref_key

			channel_id = self.bot.parse_opts_channel(pref_value)
			webhook_channel = self.bot.get_channel(channel_id)
			webhook_name = self.bot.get_webhook_name()
			webhook, error = await self.bot.get_webhook(webhook_name, webhook_channel)
			if not webhook:
				if error:
					await ctx.send(error)
					return

				webhook, error = await self.bot.create_webhook(webhook_name, self.bot.get_avatar(), webhook_channel)
				if not webhook:
					self.logger.error('create_webhook failed: %s' % error)
					await ctx.send(error)
					return

			try:
				entry = PremiumGuildConfig.objects.get(guild=guild, key=pref_key)

			except PremiumGuildConfig.DoesNotExist:
				entry = PremiumGuildConfig(guild=guild, key=pref_key)

			entry.value = channel_id
			entry.value_type = 'chan'
			entry.save()

			lines.append('`%s` %s' % (pref_key, pref_value))

		if lines:
			plural = len(lines) > 1 and 's' or ''
			plural_have = len(lines) > 1 and 'have' or 'has'
			lines.insert(0, 'The following channel%s %s been saved:' % (plural, plural_have))
			message = '\n'.join(lines)
			await ctx.send(message)

	async def set_formats(self, ctx, guild, pref_key: str, pref_value: str):

		pref_keys = self.get_matching_keys(ctx, guild, pref_key, formats=True)
		if not pref_keys:
			message = error_invalid_config_key('formats', self.bot.command_prefix, pref_key)
			await ctx.send(message)
			return

		if len(pref_keys) > 1:
			message = 'The key \'%s\' matches more than one entry:\n%s' % (pref_key, '\n'.join(pref_keys))
			await ctx.send(message)
			return

		lines = []
		for pref_key in pref_keys:

			if not pref_key.endswith('.format'):
				if pref_key not in PremiumGuild.MESSAGE_FORMATS:
					message = error_invalid_config_key('formats', self.bot.command_prefix, pref_key)
					await ctx.send(message)
					return

				pref_key = '%s.format' % pref_key

			try:
				entry = PremiumGuildConfig.objects.get(guild=guild, key=pref_key)

			except PremiumGuildConfig.DoesNotExist:
				entry = PremiumGuildConfig(guild=guild, key=pref_key)

			entry.value = pref_value
			entry.value_type = 'fmt'
			entry.save()

			lines.append('`%s` "%s"' % (pref_key, pref_value))

		if lines:
			plural = len(lines) > 1 and 's' or ''
			plural_have = len(lines) > 1 and 'have' or 'has'
			lines.insert(0, 'The following format%s %s been saved:' % (plural, plural_have))
			message = '\n'.join(lines)
			await ctx.send(message)

	async def set_mentions(self, ctx, guild, pref_key: str, pref_value: str):

		pref_keys = self.get_matching_keys(ctx, guild, pref_key, mentions=True)
		if not pref_keys:
			message = error_invalid_config_key('mentions', self.bot.command_prefix, pref_key)
			await ctx.send(message)
			return

		value = self.bot.parse_opts_boolean(pref_value)
		display_value = 'OFF'
		if value is None:
			value = self.bot.parse_opts_mention(pref_value)
			if value is None:
				message = error_invalid_config_value('mentions', self.bot.command_prefix, pref_value)
				await ctx.send(message)
				return

		discord_id = ctx.author.id
		if value is not False:
			if value is True:
				display_value = 'ON'
			else:
				discord_id = value
				display_value = '<@%s>' % discord_id

		try:
			player = Player.objects.get(discord_id=discord_id)

		except Player.DoesNotExist:
			message = 'Error: I don\'t know any allycode registered to <@%s>' % ctx.author.id
			await ctx.send(message)
			return

		lines = []
		for pref_key in pref_keys:

			player_suffix = '.%s.mention' % player.ally_code
			if not pref_key.endswith(player_suffix):
				continue

			try:
				entry = PremiumGuildConfig.objects.get(guild=guild, key=pref_key)

			except PremiumGuildConfig.DoesNotExist:
				entry = PremiumGuildConfig(guild=guild, key=pref_key)

			entry.value = value
			entry.value_type = 'hl'
			entry.save()

			display_key = pref_key.replace(player_suffix, '')
			padded_key = self.pad(display_key, MENTIONS_MAX_KEY_LEN)
			lines.append('`%s` **%s**' % (padded_key, display_value))

		if lines:
			plural = len(lines) > 1 and 's' or ''
			plural_have = len(lines) > 1 and 'have' or 'has'
			lines.insert(0, 'The following mention%s %s been saved:' % (plural, plural_have))
			message = '\n'.join(lines)
			await ctx.send(message)

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):

		if isinstance(error, commands.CommandNotFound):
			return

		raise error

	@commands.group()
	async def tracker(self, ctx):

		if ctx.invoked_subcommand is None:
			prefix = self.bot.command_prefix
			commands = [ '%s%s' % (prefix, c.qualified_name) for c in self.walk_commands() if c.qualified_name != 'tracker' ]
			message = 'The following commands are available:\n```\n%s\n```' % '\n'.join(commands)
			await ctx.send(message)

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

	@tracker.command()
	async def mentions(self, ctx, pref_key: str = None, pref_value: str = None):

		guild = self.get_guild(ctx.author)

		if pref_key and pref_value:
			return await self.set_mentions(ctx, guild, pref_key, pref_value)

		return await self.get_mentions(ctx, guild, pref_key)
