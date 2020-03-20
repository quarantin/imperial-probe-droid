#!/usr/bin/env python3

import json
from discord.ext import commands

from errors import error_invalid_config_key

import DJANGO
from swgoh.models import Player, PremiumGuild, PremiumGuildConfig

class TrackerCog(commands.Cog):

	def __init__(self, bot, config):
		self.bot = bot
		self.config = config
		self.redis = config.redis

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

	def get_matching_keys(self, guild, pref_key, config=False, channels=False, formats=False):

		keys = []
		for key, value in sorted(guild.get_config().items()):

			add = False
			if config is True and not key.endswith('.channel') and not key.endswith('.format'):
				add = True

			elif channels is True and key.endswith('.channel'):
				add = True

			elif formats is True and key.endswith('.formats'):
				add = True

			if add and pref_key in key:
				keys.append(key)

		return keys

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

		pref_keys = self.get_matching_keys(guild, pref_key, config=True)
		if not pref_keys:
			message = error_invalid_config_key(self.bot.command_prefix, pref_key)
			await ctx.send(message)
			return

		if len(pref_keys) > 1:
			pref_keys = [ '`%s`' % x for x in pref_keys if not x.endswith('.channel') and not x.endswith('format') ]
			message = '__**%s**__ matches more than one entry:\n%s' % (pref_key, '\n'.join(pref_keys))
			await ctx.send(message)
			return

		lines = []
		for pref_key in pref_keys:
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
				display_value = display_value is True and '**On**' or '**Off**'

			elif entry.value_type == 'chan':
				display_value = '<#%s>' % display_value

			lines.append('`%s` = %s' % (pref_key, display_value))

		if lines:
			plural = len(lines) > 1 and 's' or ''
			plural_have = len(lines) > 1 and 'have' or 'has'
			lines.insert(0, 'The following setting%s %s been saved:' % (plural, plural_have))
			await ctx.send('\n'.join(lines))

	async def set_channels(self, ctx, guild, pref_key: str, pref_value: str):

		pref_keys = self.get_matching_keys(guild, pref_key, channels=True)
		if not pref_keys:
			message = error_invalid_config_key(self.bot.command_prefix, pref_key)
			await ctx.send(message)
			return

		lines = []
		for pref_key in pref_keys:

			if not pref_key.endswith('.channel'):
				if pref_key != 'default' and pref_key not in PremiumGuildConfig.MESSAGE_FORMATS:
					message = error_invalid_config_key(self.bot.command_prefix, pref_key)
					await ctx.send(message)
					return

				pref_key = '%s.channel' % pref_key

			channel_id = parse_opts_channel(pref_value)
			webhook_channel = self.bot.get_channel(channel_id)
			webhook_name = self.bot.get_webhook_name(pref_key.replace('.channel', ''))
			webhook, error = await self.bot.get_webhook(webhook_name, webhook_channel)
			if not webhook:
				if error:
					await ctx.send(error)
					return

				webhook, error = await self.bot.create_webhook(webhook_name, self.bot.get_avatar(), webhook_channel)
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

			lines.append('`%s` %s' % (pref_key, pref_value))

		if lines:
			plural = len(lines) > 1 and 's' or ''
			plural_have = len(lines) > 1 and 'have' or 'has'
			lines.insert(0, 'The following channel%s %s been saved:' % (plural, plural_have))
			message = '\n'.join(lines)
			await ctx.send(message)

	async def set_formats(self, ctx, guild, pref_key: str, pref_value: str):

		pref_keys = self.get_matching_keys(guild, pref_key, formats=True)
		if not pref_keys:
			message = error_invalid_config_key(self.bot.command_prefix, pref_key)
			await ctx.send(message)
			return

		if len(pref_keys) > 1:
			message = 'The key \'%s\' matches more than one entry:\n%s' % (pref_key, '\n'.join(pref_keys))
			await ctx.send(message)
			return

		lines = []
		for pref_key in pref_keys:

			if not pref_key.endswith('.format'):
				if pref_key not in PremiumGuildConfig.MESSAGE_FORMATS:
					message = error_invalid_config_key(self.bot.command_prefix, pref_key)
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
			lines.insert(0, 'The following format%s %s been saved:' % ())
			message = '\n'.join(lines)
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
