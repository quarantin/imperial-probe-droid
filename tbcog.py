import io
import os
import json
import asyncio
import zipfile
import traceback
from datetime import datetime

import discord
from discord.ext import commands

import cog
import libswgoh
from utils import translate, translate_multi

import DJANGO
from django.db import transaction
from swgoh.models import Guild, Player
from territorybattle.models import TerritoryBattle, TerritoryBattleHistory, TerritoryBattleStat

class TBCog(cog.Cog):

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):

		if isinstance(error, commands.CommandNotFound):
			return

		raise error

	@commands.command()
	async def tbhist(self, ctx):

		player = self.options.parse_premium_user(ctx)
		if not player:
			return self.errors.not_premium()

		last_event_id = TerritoryBattle.objects.first().event_id
		data = await self.client.get_tb_history(creds_id=player.creds_id, last_event_id=last_event_id)
		if not data:
			return self.bot.errors.tb_history_failed()

		guild_id = data['guild_id']
		guild_name = data['guild_name']
		history = data['history']
		event_id = data['event_id']

		print('Parsing history for TW %s' % event_id)

		errors = False
		with transaction.atomic():

			guild, created = Guild.objects.get_or_create(guild_id=guild_id, guild_name=guild_name)
			for event in history:

				if event['type'] not in [ 'TERRITORY_CONFLICT_ACTIVITY' ]:
					continue

				try:
					o, created = TerritoryBattleHistory.parse(guild, event)
					print('Parsing %s event %s' % (event['id'], created and 'new' or 'old'))

				except Exception as err:
					errors = True
					print('Some error detected!')
					print(err)
					print(traceback.format_exc())
					print(json.dumps(event, indent=4))


		await ctx.send(errors and 'KO' or 'OK')

	@commands.command()
	async def tbstat(self, ctx):

		player = self.options.parse_premium_user(ctx)
		if not player:
			return self.errors.not_premium()

		last_event_id = TerritoryBattle.objects.first().event_id
		map_stats, guild = await self.client.get_map_stats(creds_id=player.creds_id, last_event_id=last_event_id, tb=True)

		guild_id = guild['id']
		guild_name = guild['name']

		guild, created = Guild.objects.get_or_create(guild_id=guild_id, guild_name=guild_name)

		try:
			TerritoryBattleStat.parse(guild, map_stats)
			status = 'OK'

		except Exception as err:
			status = 'ERROR'
			print(err)
			print(traceback.format_exc())

		await ctx.send(status)

	"""
	async def history(self, ctx, creds_id='anraeth'):
		
		event_id = 'TB_EVENT_GEONOSIS_SEPARATIST:O1588352400000'
		events = await self.client.get_tb_events(creds_id=creds_id, event_id=event_id)

		for event in events:

			try:
				db_event = TerritoryBattleHistory.objects.get(id=event['id'])

			except TerritoryBattleHistory.DoesNotExist:

				db_event = TerritoryBattleHistory(**event)
				db_event.save()

	# Set TB Orders
	@commands.command()
	async def stbo(self, ctx, territory=''):
		pass

	# Get TB Orders
	@commands.command()
	async def gtbo(self, ctx, creds_id='anraeth', territory='all'):

		tw = await client.get_tw_info(creds_id=creds_id)

		defend_orders = self.parse_territory(tw['defendingGuild'])
		attack_orders = self.parse_territory(tw['attackingGuild'])

		print(json.dumps(defend_orders, indent=4))
		print(json.dumps(attack_orders, indent=4))
	"""
