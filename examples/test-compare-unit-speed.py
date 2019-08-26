#!/usr/bin/env python

import os, json
from datetime import datetime
from config import load_config
from swgohhelp import fetch_guilds, api_swgoh_players, fetch_crinolo_stats
from openpyxl import Workbook
from openpyxl.styles import Font

import DJANGO
from swgoh.models import BaseUnit

config = load_config()
ally_codes = [ '349423868', '644867722' ]
project = {
	'allycodes': ally_codes,
}

def save_json(filename, jsondata):
	fout = open(filename, 'w')
	fout.write(jsondata)
	fout.close()

def load_json(filename):
	fin = open(filename, 'r')
	data = fin.read()
	fin.close()
	return json.loads(data)

if os.path.exists('custom-guilds.json'):
	print('Loading custom-guilds.json from cache...')
	guilds = load_json('custom-guilds.json')
else:
	guilds = fetch_guilds(config, project)
	jsondata = json.dumps(guilds, indent=4)
	save_json('custom-guilds.json', jsondata)

full_ally_codes = []
for ally_code in guilds:
	for ally_code, player in guilds[ally_code]['roster'].items():
		full_ally_codes.append(player['allyCode'])

if os.path.exists('custom-players.json'):
	print('Loading custom-players.json from cache...')
	players = load_json('custom-players.json')
else:
	players = api_swgoh_players(config, project={ 'allycodes': full_ally_codes })
	jsondata = json.dumps(players, indent=4)
	save_json('custom-players.json', jsondata)

if os.path.exists('custom-stats.json'):
	print('Loading custom-stats.json from cache...')
	stats = load_json('custom-stats.json')
else:
	stats, players = fetch_crinolo_stats(config, full_ally_codes, players=players)
	jsondata = json.dumps(stats, indent=4)
	save_json('custom-stats.json', jsondata)

print('Done fetching')
players_by_allycode = { x['allyCode']: x for x in players }

result = {}
base_units = sorted(list(BaseUnit.objects.all()), key=lambda x: x.name)

for unit in base_units:
	for src_ally_code in ally_codes:

		if src_ally_code in guilds:
			guild_name = guilds[src_ally_code]['name']
			guild_roster = guilds[src_ally_code]['roster']
		elif int(src_ally_code) in guilds:
			guild_name = guilds[int(src_ally_code)]['name']
			guild_roster = guilds[int(src_ally_code)]['roster']

		if guild_name not in result:
			result[guild_name] = {}

		if unit.name not in result[guild_name]:
			result[guild_name][unit.name] = []

		for ally_code_str in guild_roster:
			player = players_by_allycode[int(ally_code_str)]
			roster = { x['defId']: x for x in player['roster'] }
			if unit.base_id in roster:
				player_name = player['name']
				ally_code = player['allyCode']

				speed = 0
				if ally_code_str in stats:
					speed = stats[ally_code_str][unit.base_id]['stats']['final']['Speed']
				elif int(ally_code_str) in stats:
					speed = stats[int(ally_code_str)][unit.base_id]['stats']['final']['Speed']

				result[guild_name][unit.name].append({
					'name': player_name,
					'ally_code': ally_code,
					'speed': speed,
				})

final = {}
for guild_name, data in result.items():
	for unit_name, roster in data.items():

		if guild_name not in final:
			final[guild_name] = {}

		final[guild_name][unit_name] = sorted(roster, key=lambda x: x['speed'], reverse=True),

fout = open('final.json', 'w')
fout.write(json.dumps(final, indent=4))
fout.close()

guild_names = list(final)
guild1 = final[ guild_names[0] ]
guild2 = final[ guild_names[1] ]

def fill(list1, list2):

	len1 = len(list1)
	len2 = len(list2)

	if len1 < len2:
		diff = len2 - len1
		for i in range(0, diff):
			list1.append({'name': '', 'ally_code': '', 'speed': ''})

	if len1 > len2:
		diff = len1 - len2
		for i in range(0, diff):
			list2.append({'name': '', 'ally_code': '', 'speed': ''})


i = -1
spreadsheet = Workbook()
bold_font = Font(bold=True)

column_dims = {
	'A': 25,
	'B': 12,
	'C': 8,
	'D': 25,
	'E': 12,
	'F': 8,
}

print('Creating spreadsheet...')

for unit in base_units:
	for g1, g2 in zip(guild1[unit.name], guild2[unit.name]):

		i += 1
		sheet = spreadsheet.create_sheet(unit.name, i)

		sheet.append([ guild_names[0], '', '', guild_names[1], '', '' ])
		sheet.append([ 'Nick', 'Ally Code', 'Speed', 'Nick', 'Ally Code', 'Speed' ])

		for col, width in column_dims.items():
			sheet.column_dimensions[col].width = width

		for col in column_dims:
			for row in [ 1, 2 ]:
				cell_name = '%s%d' % (col, row)
				sheet[cell_name].font = bold_font

		fill(g1, g2)
		for p1, p2 in zip(g1, g2):
			sheet.append([ p1['name'], p1['ally_code'], p1['speed'], p2['name'], p2['ally_code'], p2['speed'] ])


date = datetime.now().strftime('%Y%m%d')
spreadsheet.save('territory-war-%s.xlsx' % date)
