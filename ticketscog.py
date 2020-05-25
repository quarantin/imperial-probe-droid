#!/usr/bin/env python3

import pytz
import json
import traceback
from datetime import datetime
from discord import Embed
from discord.ext import commands, tasks

from opts import *

import DJANGO
from django.db import transaction
from swgoh.models import Player, PlayerConfig, PlayerActivity

class TicketsCog(commands.Cog):

	max_raid_tickets = 600
	max_total_raid_tickets = 600 * 50

	def __init__(self, bot):
		self.bot = bot
		self.config = bot.config
		self.errors = bot.errors
		self.logger = bot.logger
		self.redis = bot.redis
		self.raid_tickets_notifier.start()

	def cog_unload(self):
		self.raid_tickets_notifier.cancel()

	def get_lpad_tickets(self, tickets):

		spaces = 0

		if tickets < 10:
			spaces = 2

		elif tickets < 100:
			spaces = 1

		return ' ' * spaces

	def get_raid_tickets_config(self):
		return PlayerConfig.objects.filter(key=PlayerConfig.CONFIG_NOTIFY_RAID_TICKETS)

	def get_discord_id(self, player_id):

		try:
			player = Player.objects.get(player_id=player_id)
			return '<@!%s>' % player.discord_id

		except Player.DoesNotExist:
			return None

	def store_player_activity(self, player_id, timestamp, raid_tickets, guild_tokens):

		try:
			player = Player.objects.get(player_id=player_id)

		except Player.DoesNotExist:
			print('Missing player ID from database: %s' % player_id)
			return None, None

		defaults = { 'raid_tickets': raid_tickets, 'guild_tokens': guild_tokens }

		return PlayerActivity.objects.update_or_create(player=player, timestamp=timestamp, defaults=defaults)

	async def get_guild_activity(self, creds_id=None, notify=False, store=False):

		activities = []

		total_guild_tokens = 0
		total_raid_tickets = 0
		guild = await self.bot.client.guild(creds_id=creds_id, full=True)

		guild_activity = {
			'name': guild['name'],
			'banner': guild['bannerLogo'],
			'colors': guild['bannerColor'],
			'total': {},
			'guild-tokens': {},
			'raid-tickets': {},
		}

		for member, profile in zip(guild['roster'], guild['members']):

			player_id = profile['id']
			discord_id = profile['name']

			if notify is True:
				discord_id = self.get_discord_id(player_id) or profile['name']

			stat_gt = member['activities'][1] # Guild Tokens stats
			stat_rt = member['activities'][2] # Raid Tickets stats

			guild_tokens = 'valueDaily' in stat_gt and stat_gt['valueDaily'] or 0
			raid_tickets = 'valueDaily' in stat_rt and stat_rt['valueDaily'] or 0

			total_guild_tokens += guild_tokens
			total_raid_tickets += raid_tickets

			guild_activity['guild-tokens'][discord_id] = guild_tokens
			guild_activity['raid-tickets'][discord_id] = raid_tickets

			if store is True:
				activity_reset = pytz.utc.localize(datetime.fromtimestamp(int(guild['activityReset'])))
				activity, created = self.store_player_activity(player_id, activity_reset, raid_tickets, guild_tokens)
				if activity is None:
					print('ERROR: Could not store player activity for %s (%s, %s)' % (player_id, raid_tickets, guild_tokens))
				else:
					activities.append(activity)

		guild_activity['total']['guild-tokens'] = total_guild_tokens
		guild_activity['total']['raid-tickets'] = total_raid_tickets

		if store is True and activities:
			with transaction.atomic():
				for activity in activities:
					activity.save()

		return guild_activity

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):

		if isinstance(error, commands.CommandNotFound):
			return

		raise error

	async def do_rtc(self, alert):

		creds_id = alert.player.creds_id

		guild_activity = await self.get_guild_activity(creds_id=creds_id, notify=alert.notify, store=alert.store)

		guild_name = guild_activity['name']
		guild_banner = guild_activity['banner']
		guild_colors = guild_activity['colors']
		raid_tickets = guild_activity['raid-tickets']

		miss = 0
		total = 0
		lines = []
		for name, tickets in sorted(raid_tickets.items(), key=lambda x: x[1], reverse=True):
			total += tickets
			if tickets < alert.min_tickets:
				miss += 1
				pad = self.get_lpad_tickets(tickets)
				lines.append('`| %s%d/%d |` **%s**' % (pad, tickets, alert.min_tickets, name))

		if not lines:
			lines.append('Everyone got their raid tickets done (%d/%d)! Congratulations! 🥳' % (alert.min_tickets, self.max_raid_tickets))
		else:
			#sep = self.config['separator']
			#lines = [ sep ] + lines + [ sep ]

			lines.insert(0, '__**Raid Tickets Earned**__')
			lines.insert(1, '`%d/%d` **%s**\n' % (total, self.max_total_raid_tickets, self.bot.get_percentage(total, self.max_total_raid_tickets)))

			amount = self.max_total_raid_tickets - total
			lines.insert(2, '__**Raid Tickets Missing**__')
			lines.insert(3, '`%d/%d` **%s**\n' % (amount, self.max_total_raid_tickets, self.bot.get_percentage(amount, self.max_total_raid_tickets)))

			plural = miss > 1 and 's' or ''
			lines.insert(4, '__**Missing Raid Tickets (%d player%s)**__' % (miss, plural))

		description = '\n'.join(lines)
		icon_url = 'https://swgoh.gg/static/img/assets/tex.%s.png' % guild_banner

		embed = Embed(title='', description=description)
		embed.set_author(name=guild_name, icon_url=icon_url)
		embed.set_thumbnail(url=icon_url)

		channel = self.bot.get_channel(alert.channel_id)
		await channel.send(embed=embed)

	@tasks.loop(minutes=1)
	async def raid_tickets_notifier(self):

		try:
			now = datetime.now()

			alerts = self.get_raid_tickets_config()
			for alert in alerts:

				time = datetime.strptime(alert.value, '%H:%M')

				hour_ok = now.hour == time.hour
				if not hour_ok:
					continue

				minute_ok = now.minute == time.minute
				if not minute_ok:
					continue

				await self.do_rtc(alert)

		except Exception as err:
			print(err)
			print(traceback.format_exc())
			self.logger.error(err)
			self.logger.error(traceback.format_exc())

	@commands.command(aliases=['ticket', 'tickets'])
	async def rtc(self, ctx, *, args: str = ''):

		MAX_TICKETS = 600

		notify = False
		store = False
		min_tickets = MAX_TICKETS

		args = [ x.lower() for x in args.split(' ') ]
		for arg in args:

			if arg in [ 'alert', 'alerts', 'mention', 'mentions', 'notify', 'notification', 'notifications' ]:
				notify = True

			elif arg in [ 'save', 'store' ]:
				store = True

			else:
				try:
					min_tickets = int(arg)
				except:
					pass

		if min_tickets > self.max_raid_tickets:
			min_tickets = self.max_raid_tickets

		player = parse_opts_premium_user(ctx.author)
		if not player:
			print('No premium user found')
			return self.errors.not_premium()

		alert = PlayerConfig(player=player, channel_id=ctx.channel.id, notify=notify, store=store, min_tickets=min_tickets)

		return await self.do_rtc(alert)
