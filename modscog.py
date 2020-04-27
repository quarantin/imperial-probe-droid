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
from utils import translate

import DJANGO
from swgoh.models import Player

class ModsCog(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		#self.config = bot.config
		#self.logger = bot.logger
		#self.redis = bot.redis

	def get_csv_header(self):

		headers = [ 'Equipped', 'Set', 'Slot', 'Level', 'Tier', 'Pips', 'Primary Stat Value', 'Primary Stat Name', 'Sec Stat 1 Value', 'Sec Stat 1 Name', 'Sec Stat 2 Value', 'Sec Stat 2 Name', 'Sec Stat 3 Value', 'Sec Stat 3 Name', 'Sec Stat 4 Value', 'Sec Stat 4 Name' ]

		csv = ';'.join(headers) + '\n'

		return bytes(csv, encoding='utf-8')

	def mod_to_csv(self, mod, unit):

		equipped = unit
		modset   = mod['modset']
		slot     = mod['modslot']
		level    = str(mod['level'])
		tier     = str(mod['tier'])
		pips     = str(mod['pips'])

		prim_stat_name  = mod['primaryStat']['stat']
		prim_stat_value = str(mod['primaryStat']['value'])

		sec_stat_1_name = sec_stat_1_value = ''
		sec_stat_2_name = sec_stat_2_value = ''
		sec_stat_3_name = sec_stat_3_value = ''
		sec_stat_4_name = sec_stat_4_value = ''

		if 'secondaryStat' in mod:
			sec_stats = mod['secondaryStat']

			if len(sec_stats) > 0:
				sec_stat_1_name  = sec_stats[0]['stat']
				sec_stat_1_value = str(sec_stats[0]['value'])

			if len(sec_stats) > 1:
				sec_stat_2_name  = sec_stats[1]['stat']
				sec_stat_2_value = str(sec_stats[1]['value'])

			if len(sec_stats) > 2:
				sec_stat_3_name  = sec_stats[2]['stat']
				sec_stat_3_value = str(sec_stats[2]['value'])

			if len(sec_stats) > 3:
				sec_stat_4_name  = sec_stats[3]['stat']
				sec_stat_4_value = str(sec_stats[3]['value'])

		fields = [ equipped, modset, slot, level, tier, pips, prim_stat_value, prim_stat_name, sec_stat_1_value, sec_stat_1_name, sec_stat_2_value, sec_stat_2_name, sec_stat_3_value, sec_stat_3_name, sec_stat_4_value, sec_stat_4_name ]
		csv = ';'.join(fields) + '\n'
		return bytes(csv, encoding='utf-8')

	def get_csv_file(self, init_data):

		mods = []

		for unit in init_data['roster']['units']:
			if 'mods' in unit:
				for mod in unit['mods']:
					unit_name = translate(unit['baseId'], 'eng_us')
					mods.append((unit_name, mod))

		if 'mods' in init_data['roster']:
			for mod in init_data['roster']['mods']:
				mods.append(('UNEQUIPPED', mod))

		date = datetime.now().strftime('%Y%m%d_%H%M%S')
		csv_name = '%s_mods_%s_%s.csv' % (date, init_data['playerProfile']['allyCode'], init_data['playerProfile']['playerName'].replace(' ', '_'))

		csv_data = io.BytesIO()
		csv_data.write(self.get_csv_header())
		for unit, mod in mods:
			csv_data.write(self.mod_to_csv(mod, unit))

		return csv_name, csv_data.getvalue()

	def get_zip_file(self, file_name, file_data):
		zip_filename = file_name + '.zip'
		zip_file = zipfile.ZipFile(zip_filename, mode='w', compression=zipfile.ZIP_DEFLATED)
		zip_file.writestr(file_name, file_data)
		zip_file.close()
		return zip_filename

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):

		if isinstance(error, commands.CommandNotFound):
			return

		raise error

	@commands.group()
	async def mods(self, ctx, command=''):
		session = await libswgoh.get_auth_google(creds_id='anraeth')
		init_data = await libswgoh.get_initial_data(player_id='1', session=session)
		csv_name, csv_data = self.get_csv_file(init_data)
		zip_filename = self.get_zip_file(csv_name, csv_data)
		await ctx.send(file=discord.File(zip_filename))
		os.remove(zip_filename)

async def main():
	cog = ModsCog(None)
	session = await libswgoh.get_auth_google(creds_id='anraeth')
	init_data = await libswgoh.get_initial_data(player_id='1', session=session)
	csv_name, csv_data = cog.get_csv_file(init_data)
	print(csv_data.decode('utf-8'))

if __name__ == '__main__':
	asyncio.get_event_loop().run_until_complete(main())
