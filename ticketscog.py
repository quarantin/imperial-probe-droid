#!/usr/bin/env python3

import json
from discord.ext import commands

import libswgoh

import DJANGO
from swgoh.models import Player

class TicketsCog(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.config = bot.config
		self.logger = bot.logger
		self.redis = bot.redis

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):

		if isinstance(error, commands.CommandNotFound):
			return

		raise error

	def get_discord_ids(self, player_id):

		key = 'playerid|%s' % player_id
		ally_code = self.redis.get(key)
		if not ally_code:
			return None

		result = {}
		players = Player.objects.filter(ally_code=ally_code)
		for player in players:
			result[player.game_nick] = player.discord_id

		return result

	@commands.group()
	async def tickets(self, ctx):

		tickets = {
			'guild-tokens': {},
			'raid-tickets': {},
		}

		total_guild_tokens = 0
		total_raid_tickets = 0
		session = await libswgoh.get_auth_google()
		guild = await libswgoh.get_guild(session=session)
		for member in guild['members']:

			discord_id = member['name']
			discord_ids = self.get_discord_ids(member['id'])
			if discord_id in discord_ids:
				discord_id = '<@!%s>' % discord_ids[discord_id]

			stat_gt = member['stats'][1] # Guild Token stats
			stat_rt = member['stats'][2] # Raid Tickets stats

			guild_tokens = 'valueDaily' in stat_gt and stat_gt['valueDaily'] or 0
			raid_tickets = 'valueDaily' in stat_rt and stat_rt['valueDaily'] or 0

			total_guild_tokens += guild_tokens
			total_raid_tickets += raid_tickets

			tickets['guild-tokens'][discord_id] = guild_tokens
			tickets['raid-tickets'][discord_id] = raid_tickets

		lines = []
		raid_tickets = tickets['raid-tickets']
		for name, tickets in raid_tickets.items():
			if tickets != 600:
				lines.append('`%d` __**%s**__' % (tickets, name))

		await ctx.send('\n'.join(lines))

	@tickets.command()
	async def addguild(self, ctx):
		pass
