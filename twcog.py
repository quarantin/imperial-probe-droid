#!/usr/bin/env python3

import io
import os
import json
import asyncio
import zipfile
from datetime import datetime

import discord
from discord.ext import commands

import libswgoh
from embed import new_embeds
from utils import translate, translate_multi

import DJANGO
from swgoh.models import Player

class TWCog(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		if bot:
			self.client = bot.client
			self.config = bot.config
			self.logger = bot.logger
			self.redis = bot.redis

	def get_squad_orders(self):
		fin = open('squad-orders.json', 'r')
		data = fin.read()
		fin.close()
		return json.loads(data)

	def is_same_squad(self, user_squad, ref_squad):

		ref_leader = list(ref_squad)[0]
		user_leader = list(user_squad)[0]

		if ref_leader and ref_leader != user_leader:
			return False

		for ref_unit in ref_squad:
			if ref_unit and ref_unit not in user_squad:
				return False

		return True

	def is_wrong_order(self, user_squad, ref_squad):

		for user_unit, ref_unit in zip(user_squad, ref_squad):
			if user_unit != ref_unit:
				return True

		return False

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):

		if isinstance(error, commands.CommandNotFound):
			return

		raise error

	@commands.group()
	async def wso(self, ctx, command=''):

		wrong_order = {}

		tw_squads = await self.client.get_tw_squads(creds_id='anraeth')
		squad_orders = self.get_squad_orders()
		for territory, player, squad in tw_squads:
			for ref_squad in squad_orders:
				if self.is_same_squad(squad, ref_squad) and self.is_wrong_order(squad, ref_squad):
					if player not in wrong_order:
						wrong_order[player] = {}

					if territory not in wrong_order[player]:
						wrong_order[player][territory] = []

					wrong_order[player][territory].append(squad)

		fields = []
		for player, territories in sorted(wrong_order.items()):
			value = []
			field = {
				'name': player,
				'inline': True,
			}
			for territory in libswgoh.territories_by_name:
				if territory in territories:
					squads = territories[territory]
					for squad in squads:
						value.append('__**%s**__\n```%s```' % (territory, '\n'.join(translate_multi(squad))))
			field['value'] = '\n'.join(value) + '\n'
			fields.append(field)

		msg = {
			'title': 'Wrong Squad Order',
			'fields': fields,
		}

		embeds = new_embeds(msg)
		for embed in embeds:
			await ctx.send(embed=embed)

	def parse_territory(self, data):

		orders = {}

		for territory in data['territories']:

			info = territory['info']

			territory     = info['territoryId']

			officer_order = 'orders'   in info and info['orders']   or 'No orders'
			command       = 'command'  in info and info['command']  or 'No command'

			command = command.replace('Command_', '')

			orders[territory] = (command, officer_order)

		return orders

	# Set TW Orders
	@commands.command()
	async def stwo(self, ctx, territory=''):
		pass

	# Get TW Orders
	@commands.command()
	async def gtwo(self, ctx, creds_id='anraeth', territory='all'):

		tw = await self.client.get_tw_info(creds_id=creds_id)

		defend_orders = self.parse_territory(tw['defendingGuild'])
		attack_orders = self.parse_territory(tw['attackingGuild'])

		print(json.dumps(defend_orders, indent=4))
		print(json.dumps(attack_orders, indent=4))
