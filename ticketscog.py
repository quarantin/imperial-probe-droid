#!/usr/bin/env python3

import json
import traceback
from datetime import datetime
from discord.ext import commands, tasks

from opts import *
from errors import *

import DJANGO
from swgoh.models import Player, PremiumUser, PremiumUserConfig

class TicketsCog(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.config = bot.config
		self.logger = bot.logger
		self.redis = bot.redis
		self.notifier.start()

	def cog_unload(self):
		self.notifier.cancel()

	def get_notifications(self):
		return PremiumUserConfig.objects.filter(key=PremiumUserConfig.CONFIG_NOTIFY_RAID_TICKETS)

	def get_discord_id(self, player_id):

		try:
			player = Player.objects.get(player_id=player_id)
			return '<@!%s>' % player.discord_id

		except Player.DoesNotExist:
			return None

	async def get_tickets(self, creds_id=None, notify=False):

		tickets = {
			#'total': {},
			'guild-tokens': {},
			'raid-tickets': {},
		}

		total_guild_tokens = 0
		total_raid_tickets = 0
		guild = await self.bot.client.guild(creds_id=creds_id, full=True)
		for member in guild['roster']:

			player_id = member['id']
			discord_id = member['name']

			if notify is True:
				discord_id = self.get_discord_id(player_id) or member['name']

			stat_gt = member['stats'][1] # Guild Token stats
			stat_rt = member['stats'][2] # Raid Tickets stats

			guild_tokens = 'valueDaily' in stat_gt and stat_gt['valueDaily'] or 0
			raid_tickets = 'valueDaily' in stat_rt and stat_rt['valueDaily'] or 0

			total_guild_tokens += guild_tokens
			total_raid_tickets += raid_tickets

			tickets['guild-tokens'][discord_id] = guild_tokens
			tickets['raid-tickets'][discord_id] = raid_tickets

		#tickets['total']['guild-tokens'] = total_guild_tokens
		#tickets['total']['raid-tickets'] = total_raid_tickets

		return tickets

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):

		if isinstance(error, commands.CommandNotFound):
			return

		raise error

	@tasks.loop(minutes=1)
	async def notifier(self):

		now = datetime.now()

		notifications = self.get_notifications()
		for notification in notifications:

			notif_time = datetime.strptime(notification.value, '%H:%M')
			premium_user = notification.premium_user

			hour_ok = now.hour == notif_time.hour
			minute_ok = now.minute == notif_time.minute
			if hour_ok and minute_ok:

				lines = []
				guild_tickets = await self.get_tickets(creds_id=premium_user.creds_id, notify=True)
				raid_tickets = guild_tickets['raid-tickets']

				for name, tickets in sorted(raid_tickets.items(), key=lambda x: x[1], reverse=True):
					if tickets != 600:
						lines.append('`%d` __**%s**__' % (tickets, name))


				channel = self.bot.get_channel(notification.channel_id)
				await channel.send('\n'.join(lines))

	@commands.group()
	async def tickets(self, ctx, command=''):

		tickets = {
			'guild-tokens': {},
			'raid-tickets': {},
		}

		premium_user = parse_opts_premium_user(ctx.author)
		if not premium_user:
			return error_not_premium()

		notify = command.lower() in [ 'alert', 'mention', 'notify' ]
		tickets = await self.get_tickets(creds_id=premium_user.creds_id, notify=notify)

		lines = []
		raid_tickets = tickets['raid-tickets']
		for name, tickets in sorted(raid_tickets.items(), key=lambda x: x[1], reverse=True):
			if tickets != 600:
				lines.append('`%d` __**%s**__' % (tickets, name))

		await ctx.send('\n'.join(lines))

	@tickets.command()
	async def addguild(self, ctx):
		pass
