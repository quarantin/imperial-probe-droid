#!/usr/bin/env python3

import io
import os
import json
import asyncio
import zipfile
from datetime import datetime

import discord
from discord.ext import commands

import cog
import libswgoh
from utils import translate, translate_multi

import DJANGO
from swgoh.models import Player
from territorybattle.models import TerritoryBattleHistory

class TBCog(cog.Cog):

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):

		if isinstance(error, commands.CommandNotFound):
			return

		raise error

	@commands.command()
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

async def main():
	#cog = TBCog(None)
	#session = await libswgoh.get_auth_google(creds_id='anraeth')
	pass

if __name__ == '__main__':
	asyncio.get_event_loop().run_until_complete(main())
