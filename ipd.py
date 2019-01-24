#!/usr/bin/python3

import sys
import json
import pytz
import errno
import string
import random
import discord
import datetime
import requests
import subprocess

from help import *
from lookup import *
SEPARATOR = '`------------------------------`'

SHEETS_ALIASES = {
	'a': 'allies',
	'r': 'recommendations',
}

ipd_config = {}

ipd_config_json = 'config.json'

BASE_URL = 'https://swgoh.gg/api'

BASE_IMG_URL = 'https://swgoh.gg/static/img/assets/'

def now():
	tz = pytz.timezone(ipd_config['timezone'])
	return tz.localize(datetime.datetime.now())

def basicstrip(string):
	return string.replace(' ', '').replace('"', '').replace('(', '').replace(')', '').lower()

def color(colour):
	color_code = colour in COLORS and COLORS[colour] or COLORS['red']
	return discord.Colour(color_code)

def parse_avatars():

	avatars = {}

	filename = 'avatars.csv'
	fin = open(filename, 'r')
	next(fin)

	for line in fin:

		toks = line.strip().split(';')
		if len(toks) != 2:
			raise Exception('Invalid line: %s in file %s' % (line, filename))

		unit_name  = toks[0]
		avatar_url = toks[1]

		avatars[unit_name] = '%s%s' % (BASE_IMG_URL, avatar_url)

	return avatars

def get_swgoh_profile_url(ally_code):

	url = 'https://swgoh.gg/p/%s/' % ally_code
	try:
		response = requests.head(url)
		if response.status_code == 200:
			return url
	except:
		pass

	return 'No profile found on swgoh.gg'

def download_spreadsheet(url, cols):

	content = []
	response = requests.get(url)
	response.encoding = 'utf-8'

	lines = response.text.split('\r\n')
	for line in lines:
		toks = line.split(',')
		content.append(toks[0:cols])

	return iter(content)

def parse_allies_db():

	url = ipd_config['sheets']['allies']['view']

	allies_db = {}
	allies_db['by-ally-code'] = {}
	allies_db['by-game-nick'] = {}
	allies_db['by-discord-nick'] = {}

	allies = download_spreadsheet(url, 3)
	next(allies)

	for ally in allies:

		game_nick, discord_nick, ally_code = ally

		allies_db['by-ally-code'][ally_code] = ally
		allies_db['by-game-nick'][game_nick] = ally
		allies_db['by-discord-nick'][discord_nick] = ally

	return allies_db

def parse_recommendations():

	url = ipd_config['sheets']['recommendations']['view']

	recos_db = {}
	recos_db['by-source'] = {}

	recos = download_spreadsheet(url, 12)
	next(recos)

	for reco in recos:

		name = basicstrip(reco[0])
		source = reco[1]

		if source not in recos_db['by-source']:
			recos_db['by-source'][source] = {}

		if name not in recos_db:
			recos_db[name] = []

		if name not in recos_db['by-source'][source]:
			recos_db['by-source'][source][name] = []

		recos_db[name].append(reco)
		recos_db['by-source'][source][name].append(reco)

	return recos_db

def parse_units(db, combat_type=None):

	units = db['units']

	new_units = {}
	new_units['by-id'] = {}
	new_units['by-name'] = {}

	for unit in units:

		unit = unit['data']
		name = unit['name']
		base_id = unit['base_id']

		if not combat_type or combat_type == unit['combat_type']:
			new_units['by-id'][base_id] = unit
			new_units['by-name'][name] = unit

	return new_units

def parse_mods(db):

	mods = {}
	stats = {}

	for modset_id, modset_name in MODSETS.items():
		mods[modset_name] = {}

		for shape_id, shape_name in MODSLOTS.items():
			mods[modset_name][shape_name] = {}

			key = '%s-%s' % (modset_name, shape_name)

			stats[modset_name] = 0
			stats[key] = 0

	for mod in db['mods']:

		modset = MODSETS[ mod['set'] ]
		modslot = MODSLOTS[ mod['slot'] ]
		modprimary = mod['primary_stat']['name']
		if modprimary not in mods[modset][modslot]:
			mods[modset][modslot][modprimary] = 0

		key = '%s-%s' % (modset, modslot)

		stats[modset] = stats[modset] + 1
		stats[key] = stats[key] + 1

		mods[modset][modslot][modprimary] = mods[modset][modslot][modprimary] + 1

	return mods, stats

def parse_unit_mods(units, mods):

	for mod in mods['mods']:

		base_id = mod['character']
		unit = units['by-id'][base_id]
		if 'mods' not in unit:
			unit['mods'] = []

		unit['mods'].append(mod)

	for base_id, unit in units['by-id'].items():

		if 'mods' not in unit:
			continue

		mods = unit['mods']

		modsets = {}
		modslots = {}
		for mod in mods:

			modset = mod['modset'] = MODSETS[ mod['set'] ]
			modslot = mod['modslot'] = MODSLOTS[ mod['slot'] ]

			if modset not in modsets:
				modsets[modset] = 0

			modsets[modset] = modsets[modset] + 1
			modslots[modslot] = mod

		for modset, count in dict(modsets).items():
			count = int(count / MODSETS_NEEDED[modset])
			modsets[modset] = count

		real_modsets = []
		for modset, count in dict(modsets).items():
			for i in range(0, count):
				real_modsets.append(modset)

		real_modsets = sorted(real_modsets)

		while len(real_modsets) < 3:
			real_modsets.append('')

		unit['modsets'] = real_modsets
		unit['modslots'] = modslots

def api_units(ally_code):

	url = '%s/player/%s/' % (BASE_URL, ally_code)

	response = requests.get(url)

	return response.json()

def api_mods(ally_code):

	url = '%s/players/%s/mods/' % (BASE_URL, ally_code)

	response = requests.get(url)

	return response.json()

def get_player_units(ally_code):

	db = api_units(ally_code)

	return parse_units(db)

def get_player_characters(ally_code):

	db = api_units(ally_code)

	return parse_units(db, combat_type=1)

def get_player_ships(ally_code):

	db = api_units(ally_code)

	return parse_units(db, combat_type=2)

def get_all_character_names(ally_code):

	units = get_player_characters(ally_code)

	return sorted(units['by-name'])

def get_all_ship_names(ally_code):

	units = get_player_ships(ally_code)

	return sorted(units['by-name'])

def format_char_stats(unit, fmt):

	stats = unit['stats']

	for pat, key in STATS_LUT.items():

		pattern = '%%%s' % pat

		if pattern in fmt:

			data = stats[key]
			if pat in [ 'critical-damage' , 'potency','tenacity' ]:
				data = 100 * data

			data = round(data)

			if pat in PERCENT_STATS:
				data = '%d%%' % data

			fmt = fmt.replace(pattern, str(data)).replace('%20', ' ').replace('%0A', '\n')

	return fmt

def format_char_details(unit, fmt):

	for pat, key in FORMAT_LUT.items():

		pattern = '%%%s' % pat

		if pattern in fmt:
			fmt = fmt.replace(pattern, str(unit[key]))

	return fmt

def get_arena_team(ally_code, fmt):

	arena_team = []

	db = api_units(ally_code)

	if 'units' not in db:
		return None, None, None

	units = parse_units(db, combat_type=1)

	arena = db['data']['arena']

	leader = arena['leader']
	members = arena['members']

	for base_id in members:

		unit = units['by-id'][base_id]

		fmt_cpy = str(fmt)
		fmt_cpy = format_char_details(unit, fmt_cpy)
		fmt_cpy = format_char_stats(unit, fmt_cpy)

		leader_str = ''
		if base_id == leader:
			leader_str = ' (Leader)'

		fmt_cpy = fmt_cpy.replace('%leader', leader_str)

		arena_team.append(fmt_cpy)

	return db['data']['name'], arena['rank'], arena_team

def get_fleet_arena_team(ally_code, fmt):

	arena_team = []

	db = api_units(ally_code)

	if 'units' not in db:
		return None, None, None

	units = parse_units(db, combat_type=2)

	arena =  db['data']['fleet_arena']

	leader = arena['leader']
	members = arena['members'] + arena['reinforcements']

	for base_id in members:

		unit = units['by-id'][base_id]

		fmt_cpy = str(fmt)
		fmt_cpy = format_char_details(unit, fmt_cpy)
		fmt_cpy = format_char_stats(unit, fmt_cpy)

		leader_str = ''
		if base_id == leader:
			leader_str = ' (Leader)'

		fmt_cpy = fmt_cpy.replace('%leader', leader_str)

		arena_team.append(fmt_cpy)

	return db['data']['name'], arena['rank'], arena_team

fmt_lite = '**%name**%leader\n  **P**:%power **L**:%level **G**:%gear **H**:%health **P**:%protection **S**:%speed **T**:%tenacity **P**:%potency **CD**:%critical-damage\n'
fmt_short = '**%name**%leader\n  **Power:**%power **Level:**%level **Gear:**%gear\n  **H:**%health **Pr:**%protection **S:**%speed\n  **T:**%tenacity **Po:**%potency **CD:**%critical-damage\n'

fmt_long = '\n'.join([
	'**%name**%leader',
	'  **Power**:      %power',
	'  **Level**:      %level',
	'  **Gear**:       %gear',
	'  **Health**:     %health',
	'  **Protection**: %protection',
	'  **Speed**:      %speed',
	'  **Potency**:    %potency',
	'  **Tenacity**:   %tenacity',
	'  **CD**:         %critical-damage',
	'  **CC (phy)**:   %physical-critical-chance',
	'  **CC (spe)**:   %special-critical-chance',
	'  **Armor**:      %armor',
	'  **Resistance**: %resistance',
	''
])

async def send_embed(channel, msg, timestamp=None):

	if timestamp is None:
		timestamp = now()

	if 'color' not in msg:
		msg['color'] = 'blue'

	if 'title' not in msg:
		msg['title'] = ''

	if 'description' not in msg:
		msg['description'] = ''

	embed = discord.Embed(title=msg['title'], colour=color(msg['color']), description=msg['description'], timestamp=timestamp)

	if 'author' in msg:
		embed.set_author(name=msg['author']['name'], icon_url=msg['author']['icon_url'])

	if 'image' in msg:
		embed.set_image(url=msg['image'])

	if 'thumbnail' in msg:
		embed.set_thumbnail(url=msg['thumbnail'])

	if 'fields' in msg:
		for field in msg['fields']:

			if 'name' not in field:
				field['name'] = ''

			if 'value' not in field:
				field['value'] = ''

			if 'inline' not in field:
				field['inline'] = False

			embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

	await bot.send_message(channel, embed=embed)

async def parse_opts_ally_codes(author, channel, args):

	ally_codes = []
	args_cpy = list(args)

	for arg in args_cpy:

		if len(arg) >= 9 and arg.isdigit():
			args.remove(arg)
			ally_codes.append(arg)

	if not ally_codes:

		if author in ALLIES_DB['by-discord-nick']:
			ally_codes.append(ALLIES_DB['by-discord-nick'][author][2])

		else:
			msg = {
				'title': 'Not found',
				'color': 'red',
				'description': 'No ally code specified, or found registered to <%s>' % author,
			}

			await send_embed(channel, msg)

	return args, ally_codes

def substitute_tokens(text):

	tokens = [
		'authors',
		'prefix',
		'source',
	]

	for token in tokens:

		value = ipd_config[token]
		if type(value) is list:
			value = ', '.join(value)

		text = text.replace('%' + token, value)

	return text

async def cmd_help(author, channel, args):

	msg = HELP_HELP

	if args:
		command = args[0]
		if command in HELP_MESSAGES:
			msg = HELP_MESSAGES[command]

	msg['title'] = substitute_tokens(msg['title'])
	msg['description'] = substitute_tokens(msg['description'])

	await send_embed(channel, msg)

async def cmd_arena(author, channel, args):

	fmt = fmt_short

	args, ally_codes = await parse_opts_ally_codes(author, channel, args)
	if not ally_codes:
		return

	arg_iter = iter(args)

	for arg in arg_iter:

		if arg in [ 'l', 'lite' ]:
			fmt = fmt_lite

		elif arg in [ 's', 'short' ]:
			fmt = fmt_short

		elif arg in [ 'v', 'verbose' ]:
			fmt = fmt_long

		elif arg in [ 'c', 'custom' ]:
			fmt = next(arg_iter)

	for ally_code in ally_codes:

		player, rank, team = get_arena_team(ally_code, fmt)

		if player:
			msg = {
				'title': 'Arena team of %s (Rank: %s)\n%s' % (player, rank, get_swgoh_profile_url(ally_code)),
				'color': 'blue',
				'description': '\n'.join(team),
			}
		else:
			url = 'https://swgoh.gg/p/%s/' % ally_code
			msg = {
				'title': 'Not found',
				'color': 'red',
				'description': 'Are you sure `%s` is a valid ally code and the account actually exists on swgoh.gg? Please check this URL to see: %s' % (ally_code, url)
			}

		await send_embed(channel, msg)

async def cmd_alias(author, channel, args):

	lines = []
	prefix = ipd_config['prefix']

	if not args:

		i = 1
		for alias, command in sorted(ipd_config['aliases'].items()):
			lines.append('**[%d]** **%s%s** `%s`' % (i, prefix, alias, command))
			i = i + 1

		lines = [ SEPARATOR ] + lines + [ SEPARATOR ]
		await send_embed(channel, {
			'title': 'Alias List',
			'description': '\n'.join(lines),
		})
		return

	action = args[0]

	if action == 'del':

		if len(args) < 2:
			await send_embed(channel, {
				'title': 'Missing Parameters',
				'color': 'red',
				'description': 'Please see !help alias.',
			})
			return

		alias_name = args[1]
		if alias_name.isdigit():
			alias_name = int(alias_name)

			i = 1
			for alias, command in sorted(ipd_config['aliases'].items()):
				if i == alias_name:
					del ipd_config['aliases'][alias]
					break

				i = i + 1
		elif alias_name in ipd_config['aliases']:
			del ipd_config['aliases'][alias_name]

		save_config()
		await send_embed(channel, {
			'title': 'Delete alias',
			'description': 'The alias was deleted!',
		})
		return

	elif action == 'add':

		if len(args) < 3:
			await send_embed(channel, {
				'title': 'Missing Parameters',
				'color': 'red',
				'description': 'Please see !help alias.',
			})
			return

		alias_name = args[1]
		alias_command = ' '.join(args[2:])
		if alias_command.startswith(ipd_config['prefix']):
			alias_command = alias_command[1:]

		ipd_config['aliases'][alias_name] = alias_command

		save_config()
		await send_embed(channel, {
			'title': 'Add alias',
			'description': 'The alias was added!',
		})
		return

	msg = {
		"TODO": "TODO",
	}
	await send_embed(channel, msg)

async def cmd_fleet_arena(author, channel, args):

	fmt = fmt_short

	args, ally_codes = await parse_opts_ally_codes(author, channel, args)
	if not ally_codes:
		return

	arg_iter = iter(args)

	for arg in arg_iter:

		if arg in [ 'l', 'lite' ]:
			fmt = fmt_lite

		elif arg in [ 's', 'short' ]:
			fmt = fmt_short

		elif arg in [ 'v', 'verbose' ]:
			fmt = fmt_long

		elif arg in [ 'c', 'custom' ]:
			fmt = next(arg_iter)

	for ally_code in ally_codes:

		player, rank, team = get_fleet_arena_team(ally_code, fmt)

		msg = {
			'title': 'Fleet arena team of %s (Rank: %d)\n%s' % (player, rank, get_swgoh_profile_url(ally_Code)),
			'color': 'blue',
			'description': '\n'.join(team),
		}

		await send_embed(channel, msg)

async def cmd_mods(author, channel, args):

	action = ''

	args, ally_codes = await parse_opts_ally_codes(author, channel, args)
	if not ally_codes:
		return

	for arg in args:

		if arg in [ 's', 'stats' ]:
			action = 'stats'

		elif arg in [ 'm', 'missing' ]:
			action = 'missing'

		elif arg in [ 'i', 'incomplete' ]:
			action = 'incomplete'

	for ally_code in ally_codes:

		info = api_units(ally_code)
		mods = api_mods(ally_code)

		units = parse_units(info)

		player = info['data']['name']

		if action == 'missing':

			for mod in mods['mods']:

				base_id = mod['character']
				unit = units['by-id'][base_id]
				if 'mods' not in unit:
					unit['mods'] = []

				unit['mods'].append(mod)

			lines = []
			for base_id, unit in units['by-id'].items():

				if 'mods' not in unit:

					#if unit['level'] >= 50:
					#	output = '%s has no mods.' % unit['name']
					#	lines.append(output)

					continue

				count = len(unit['mods'])
				if count < 6:
					output = '  - %d mods missing for %s.' % ((6 - count), unit['name'])
					lines.append(output)

			if len(lines) == 0:
				msg = {
					'title': 'Mods info',
					'color': 'blue',
					'description': 'No characters with missing mods.',
				}
				await send_embed(channel, msg)

			else:
				msg = {
					'title': 'Mods info',
					'color': 'blue',
					'description': '%s has %d characters with missing mods:\n%s' % (info['data']['name'], len(lines), '\n'.join(sorted(lines))),
				}
				await send_embed(channel, msg)

		elif action == 'incomplete':
			pass

		else:
			msg = {
				'title': 'Mods info',
				'color': 'blue',
				'description': '%s has %d equipped mods.' % (player, mods['count']),
			}
			await send_embed(channel, msg)

async def cmd_mods_needed(author, channel, args):

	modsets = {}

	for source, names in RECOS_DB['by-source'].items():

		new_modsets = {}
		for name, recos in names.items():
			amount = len(recos)
			for reco in recos:

				sets = []

				sets.append(reco[3])
				sets.append(reco[4])
				if reco[5]:
					sets.append(reco[5])

				for aset in sets:
					if aset not in new_modsets:
						new_modsets[aset] = 0.0
					new_modsets[aset] = new_modsets[aset] + 1.0 / amount

		for aset, count in new_modsets.items():

			if aset not in modsets:
				modsets[aset] = {}

			if source not in modsets[aset]:
				modsets[aset][source] = 0.0

			modsets[aset][source] = modsets[aset][source] + count

	lines = []
	for aset in MODSET_LIST:
		sources = modsets[aset]
		counts = []
		for source, count in sorted(sources.items()):
			modset_emoji = EMOJIS[ aset.replace(' ', '').lower() ]
			#source_emoji = EMOJIS[ source.replace(' ', '').lower() ]
			counts.append('x %.3g' % count)

		lines.append('%s `%s`' % (modset_emoji, ' | '.join(counts)))

	sources = sorted(list(RECOS_DB['by-source']))
	src_emojis = []
	spacer = EMOJIS['']
	for source in sources:
		emoji = EMOJIS[ source.replace(' ', '').lower() ]
		src_emojis.append(spacer)
		src_emojis.append(emoji)

	emojis = ''.join(src_emojis)
	lines = [ emojis ] + lines

	lines = [ SEPARATOR ] + lines + [ SEPARATOR ]

	await send_embed(channel, {
		'title': 'Modsets needed',
		'description': '\n'.join(lines),
	})

def parse_opts_unit_names(units, args, combat_type=1):

	selected_units = []
	new_args = list(args)

	for arg in new_args:

		if len(arg) < 2:
			continue

		larg = basicstrip(arg)
		if larg in UNITS_SHORT_NAMES:
			larg = basicstrip(UNITS_SHORT_NAMES[larg])

		found = False
		for base_id, unit in sorted(units['by-id'].items()):

			if unit['combat_type'] != combat_type:
				continue


			name1 = basicstrip(unit['name'])
			name2 = name1.replace('î', 'i').replace('Î', 'i')
			name3 = name1.replace('-', '')
			name4 = name1.replace('\'', '')

			if larg in name1 or larg in name2 or larg in name3 or larg in name4:
				selected_units.append(unit)
				found = True

		if found:
			args.remove(arg)

	return args, selected_units

async def cmd_mods_recommendations(author, channel, args):

	max_modsets = 2

	args, ally_codes = await parse_opts_ally_codes(author, channel, args)
	if not args:
		msg = {
			'title': 'Missing unit name',
			'color': 'red',
			'description': 'You have to provide at least one unit name.',
		}
		await send_embed(channel, msg)
		return

	for ally_code in ally_codes:

		discord_id = None
		if ally_code in ALLIES_DB['by-ally-code']:
			discord_id = ALLIES_DB['by-ally-code'][ally_code][1]

		info = api_units(ally_code)
		mods = api_mods(ally_code)
		units = parse_units(info)
		parse_unit_mods(units, mods)

		new_args, selected_units = parse_opts_unit_names(units, list(args))
		if new_args:
			msg = {
				'title': 'Unknown parameter(s)',
				'color': 'red',
				'description': 'I don\'t know what to do with the following parameter(s):\n - %s' % '\n - '.join(new_args),
			}
			await send_embed(channel, msg)
			return

		player = info['data']['name']

		for unit in selected_units:

			name = basicstrip(unit['name'])
			if name in RECOS_DB:
				recos = RECOS_DB[name]
				lines = []

				for reco in recos:

					source   = EMOJIS[ reco[1].replace(' ', '').lower() ]

					info     = reco[2].strip()

					set1     = EMOJIS[ reco[3].replace(' ', '').lower() ]
					set2     = EMOJIS[ reco[4].replace(' ', '').lower() ]
					set3     = EMOJIS[ reco[5].replace(' ', '').lower() ]

					square   = SHORT_STATS[ reco[6].strip()  ]
					arrow    = SHORT_STATS[ reco[7].strip()  ]
					diamond  = SHORT_STATS[ reco[8].strip()  ]
					triangle = SHORT_STATS[ reco[9].strip()  ]
					circle   = SHORT_STATS[ reco[10].strip() ]
					cross    = SHORT_STATS[ reco[11].strip() ]

					info = info and ' (%s)' % info or ''

					#line = '%s%s%s%s%s|%s|%s|%s|%s|%s%s' % (source, set1, set2, set3, square, arrow, diamond, triangle, circle, cross, info)
					line = '%s%s%s%s`%s|%s|%s|%s`%s' % (source, set1, set2, set3, arrow, triangle, circle, cross, info)
					lines.append(line)

				lines.append('------------------------------')

				if 'modsets' in unit and len(unit['modsets']) > 0:
					source   = EMOJIS['crimsondeathwatch']

					info     = ' %s' % (discord_id or ally_code)

					set1     = EMOJIS[ unit['modsets'][0].replace(' ', '').lower() ]
					set2     = EMOJIS[ unit['modsets'][1].replace(' ', '').lower() ]
					set3     = EMOJIS[ unit['modsets'][2].replace(' ', '').lower() ]

					square   = 'Square'   in unit['modslots'] and SHORT_STATS[ unit['modslots']['Square']['primary_stat']['name'] ]   or '??'
					arrow    = 'Arrow'    in unit['modslots'] and SHORT_STATS[ unit['modslots']['Arrow']['primary_stat']['name'] ]    or '??'
					diamond  = 'Diamond'  in unit['modslots'] and SHORT_STATS[ unit['modslots']['Diamond']['primary_stat']['name'] ]  or '??'
					triangle = 'Triangle' in unit['modslots'] and SHORT_STATS[ unit['modslots']['Triangle']['primary_stat']['name'] ] or '??'
					circle   = 'Circle'   in unit['modslots'] and SHORT_STATS[ unit['modslots']['Circle']['primary_stat']['name'] ]   or '??'
					cross    = 'Cross'    in unit['modslots'] and SHORT_STATS[ unit['modslots']['Cross']['primary_stat']['name'] ]    or '??'

					#line = '%s%s%s%s%s|%s|%s|%s|%s|%s%s' % (source, set1, set2, set3, square, arrow, diamond, triangle, circle, cross, info)
					line = '%s%s%s%s`%s|%s|%s|%s`%s' % (source, set1, set2, set3, arrow, triangle, circle, cross, info)

				else:
					line = '%s has no mods (%s)' % (unit['name'], discord_id or ally_code)

				lines.append(line)
				lines.append('------------------------------')

				spacer = EMOJIS[''] * 4

				line = '%s%s%s%s%s' % (spacer, EMOJIS['arrow'], EMOJIS['triangle'], EMOJIS['circle'], EMOJIS['cross'])
				lines =  [ line ] + lines

				avatar_url = AVATARS_DB[ unit['name'] ]

				msg = {
					'title': 'Recommended mods',
					'author': {
						'name': unit['name'],
						'icon_url': avatar_url,
					},
					#'image': avatar_url,
					'thumbnail': avatar_url,
					'color': 'blue',
					'description': '\n'.join(lines),
				}
				await send_embed(channel, msg)
			else:
				msg = {
					'title': 'No recommended mods',
					'color': 'red',
					'description': '%s is missing from the recommendation spreadsheet' % unit['name'],
				}
				await send_embed(channel, msg)

async def cmd_sheets(author, channel, args):

	sheets = {}
	for arg in args:

		if arg in SHEETS_ALIASES:
			arg = SHEETS_ALIASES[arg]

		if arg in ipd_config['sheets']:
			sheets[arg] = ipd_config['sheets'][arg]

	if not sheets:
		sheets = ipd_config['sheets']

	lines = []
	for name, urls in sorted(sheets.items()):
		lines.append('**`%s`**: %s' % (name, urls['edit']))

	msg = {
		'title': '',
		'color': 'blue',
		'description': '\n'.join(lines),
	}

	await send_embed(channel, msg)

MODSET_OPTS = {
	'he':              'Health',
	'health':          'Health',
	'de':              'Defense',
	'defense':         'Defense',
	'po':              'Potency',
	'potency':         'Potency',
	'te':              'Tenacity',
	'tenacity':        'Tenacity',
	'cc':              'Critical Chance',
	'critical-chance': 'Critical Chance',
	'cd':              'Critical Damage',
	'critical-damage': 'Critical Damage',
	'of':              'Offense',
	'offense':         'Offense',
	'sp':              'Speed',
	'speed':           'Speed',
}

MODSHAPE_OPTS = {
	'sq':       'Square',
	'square':   'Square',
	'ar':       'Arrow',
	'arrow':    'Arrow',
	'di':       'Diamond',
	'diamond':  'Diamond',
	'tr':       'Triangle',
	'triangle': 'Triangle',
	'ci':       'Circle',
	'circle':   'Circle',
	'cr':       'Cross',
	'cross':    'Cross',
}

def count_mods_per_shape(mod_shapes):

	shape_count = {}

	for modset, shapes in mod_shapes.items():
		for shape, count in shapes.items():
			if shape not in shape_count:
				shape_count[shape] = 0

			shape_count[shape] = shape_count[shape] + count

	return shape_count

def parse_mod_counts(mods):

	count = {}
	shapes = {}
	primaries = {}

	for mod in mods:

		modset = MODSETS[ mod['set'] ]
		if modset not in count:
			count[modset] = 0
			shapes[modset] = {}
			primaries[modset] = {}
		count[modset] = count[modset] + 1

		shape = MODSLOTS[ mod['slot'] ]
		if shape not in shapes[modset]:
			shapes[modset][shape] = 0
			primaries[modset][shape] = {}
		shapes[modset][shape] = shapes[modset][shape] + 1

		primary = mod['primary_stat']['name']
		if primary not in primaries[modset][shape]:
			primaries[modset][shape][primary] = 0
		primaries[modset][shape][primary] = primaries[modset][shape][primary] + 1

	return count, shapes, primaries

def parse_opts_modsets(args):

	selected_modsets = []
	args_cpy = list(args)
	for arg in args_cpy:
		if arg in MODSET_OPTS:
			args.remove(arg)
			modset = MODSET_OPTS[arg]
			if modset not in selected_modsets:
				selected_modsets.append(modset)

	return args, selected_modsets

def parse_opts_modshapes(args):

	selected_modshapes = []
	args_cpy = list(args)
	for arg in args_cpy:
		if arg in MODSHAPE_OPTS:
			args.remove(arg)
			modshape = MODSHAPE_OPTS[arg]
			if modshape not in selected_modshapes:
				selected_modshapes.append(modshape)

	return args, selected_modshapes

async def cmd_stats(author, channel, args):

	args, ally_codes = await parse_opts_ally_codes(author, channel, args)

	args, selected_modsets = parse_opts_modsets(args)

	args, selected_modshapes = parse_opts_modshapes(args)

	if args:
		msg = {
			'title': 'Unknown parameter(s)',
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter(s):\n - %s' % '\n - '.join(args),
		}

		await send_embed(channel, msg)
		return

	for ally_code in ally_codes:

		info = api_units(ally_code)
		mods = api_mods(ally_code)
		units = parse_units(info)
		parse_unit_mods(units, mods)

		counts, shapes, primaries = parse_mod_counts(mods['mods'])

		player = info['data']['name']
		equipped_mods = len(mods['mods'])

		if not selected_modsets and not selected_modshapes:

			lines = []

			shape_count = count_mods_per_shape(shapes)
			for shape in [ 'Square', 'Arrow', 'Diamond', 'Triangle', 'Circle', 'Cross' ]:
				count = shape_count[shape]
				emoji = EMOJIS[shape.replace(' ', '').lower()]
				lines.append('%s x %d mods' % (emoji, count))

			lines.append(SEPARATOR)

			for modset in MODSET_LIST:
				count = counts[modset]
				emoji = EMOJIS[modset.replace(' ', '').lower()]
				modset_group = MODSETS_NEEDED[modset]
				modsets, remainder = divmod(count, modset_group)
				remain = remainder > 0 and ' + %d mod(s)' % remainder or ''
				pad1 = ''
				if count < 100:
					pad1 = u'\u202F\u202F'
				if count < 10:
					pad1 = pad1 * 2

				pad2 = ''
				if modsets < 100:
					pad2 = u'\u202F\u202F'
				if modsets < 10:
					pad2 = pad2 * 2

				lines.append('%s `x %s%d mods = %s%d modsets%s`' % (emoji, pad1, count, pad2, modsets, remain))

			lines = [ SEPARATOR ] + lines + [ SEPARATOR ]

			msg = {
				'title': '%s Mods Statistics' % player,
				'description': 'Equipped mods: **%d**\n%s' % (equipped_mods, '\n'.join(lines)),
			}

			await send_embed(channel, msg)
			return

		if selected_modsets and not selected_modshapes:

			for modset in selected_modsets:

				lines = []
				total_for_modset = 0
				for shape in [ 'Square', 'Arrow', 'Diamond', 'Triangle', 'Circle', 'Cross' ]:
					if shape in shapes[modset]:
						modset_emoji = EMOJIS[modset.replace(' ', '').lower()]
						modshape_emoji = EMOJIS[shape.replace(' ', '').lower()]
						count = shapes[modset][shape]
						pad = ''
						if count < 100:
							pad = u'\u202F\u202F'
						if count < 10:
							pad = pad * 2

						total_for_modset = total_for_modset + count

						line = '%s%s `x %s%d`' % (modset_emoji, modshape_emoji, pad, shapes[modset][shape])
						lines.append(line)

				lines = [ SEPARATOR ] + lines + [ SEPARATOR ]

				msg = {
					'title': '%s %s Mods Statistics' % (player, modset),
					'description': 'Equipped %s mods: %d\n%s' % (modset.lower(), total_for_modset, '\n'.join(lines)),
				}

				await send_embed(channel, msg)
			return

		if not selected_modsets and selected_modshapes:

			lines = []
			pad = '\u202f' * 4
			for modset in MODSET_LIST:
				for shape in selected_modshapes:
					modset_emoji = EMOJIS[modset.replace(' ', '').lower()]
					modshape_emoji = EMOJIS[shape.replace(' ', '').lower()]

					sublines = []
					total_for_shape = 0
					desc = 'Equipped %s %s mods' % (modset_emoji, modshape_emoji)
					for primary, count in sorted(primaries[modset][shape].items()):
						total_for_shape = total_for_shape + count
						sublines.append('%s`%d x %s`' % (pad, count, primary))

					desc = '%s %s x %d' % (modset_emoji, modshape_emoji, total_for_shape)

					lines.append(desc)
					lines = lines + sublines

			lines = [ SEPARATOR ] + lines + [ SEPARATOR ]

			msg = {
				'title': '%s Mods Statistics' % player,
				'description': '\n'.join(lines),
			}

			await send_embed(channel, msg)
			return

		lines = []
		total_for_shape = 0
		for modset in selected_modsets:
			for shape in selected_modshapes:
				modset_emoji = EMOJIS[modset.replace(' ', '').lower()]
				modshape_emoji = EMOJIS[shape.replace(' ', '').lower()]
				for primary, count in primaries[modset][shape].items():
					pad = ''
					if count < 100:
						pad = u'\u202F\u202F'
					if count < 10:
						pad = pad * 2

					total_for_shape = total_for_shape + count
					line = '%s%s%s `x %s%d`' % (modset_emoji, modshape_emoji, primary, pad, count)
					lines.append(line)

		lines = [ SEPARATOR ] + lines + [ SEPARATOR ]

		msg = {
			'title': '%s %s %s Mods Primaries' % (player, modset, shape),
			'description': 'Equipped %s %s mods: %d\n%s' % (modset.lower(), shape.lower(), total_for_shape, '\n'.join(lines)),
		}
		await send_embed(channel, msg)

def update_source_code():

	#subprocess.call([ 'git', 'reset', '--hard'])
	subprocess.call([ 'git', 'stash' ])
	subprocess.call([ 'git', 'fetch'])
	subprocess.call([ 'git', 'pull', 'origin', 'master'])

def exit_bot():

	bot.logout()
	bot.close()

	print('Restarting!')
	sys.exit()

async def cmd_update(author, channel, args):

	if author not in ipd_config['admins']:

		msg = {
			'title': 'Unauthorized Command',
			'color': 'red',
			'description': 'You are not allowed to run this command because you are not an administrator.',
		}

		await send_embed(channel, msg)
		return

	update_source_code()
	exit_bot()

async def cmd_restart(author, channel, args):

	if author not in ipd_config['admins']:

		msg = {
			'title': 'Unauthorized Command',
			'color': 'red',
			'description': 'You are not allowed to run this command because you are not an administrator.',
		}

		await send_embed(channel, msg)
		return

	exit_bot()

def write_json_to_file(jsondata, filename):

	fin = open(filename, 'w')
	fin.write(json.dumps(jsondata, indent=4, sort_keys=True))
	fin.close()

def save_config():

	write_json_to_file(ipd_config, ipd_config_json)

def load_config():

	fin = open(ipd_config_json, 'r')
	jsonstr = fin.read()
	fin.close()

	jsondata = json.loads(jsonstr)

	ipd_config.clear()
	ipd_config.update(jsondata)
	print(json.dumps(ipd_config, indent=4, sort_keys=True))

bot = discord.Client()

def say_hello_helper(word):

	for c in string.ascii_uppercase:

		if c in word:
			rand_count = random.randrange(2, 7)
			word = word.replace(c, c.lower() * rand_count)

	return word

async def say_hello():

	words = []
	chan_id = '533305966632894505'
	word_count = random.randrange(3, 10)
	words_ref = list(PROBE_DIALOG)

	for i in range(0, word_count):

		rand_index = random.randrange(0, len(PROBE_DIALOG))
		rand_word = PROBE_DIALOG[rand_index]

		words.append(say_hello_helper(rand_word))

	message = ' '.join(words)
	channel = bot.get_channel(chan_id)
	await bot.send_message(channel, message.capitalize())

@bot.event
async def on_ready():
	print('Logged in as %s (ID:%s)' % (bot.user.name, bot.user.id))
	await say_hello()

@bot.event
async def on_message(message):

	if not message.content.startswith(ipd_config['prefix']):
		return

	channel = message.channel
	nick = message.author.nick or message.author.id
	author = '@%s' % nick
	args = message.content.strip().split(' ')
	command = args[0][1:]
	if command in ipd_config['aliases']:
		args = message.content.replace(command, ipd_config['aliases'][command]).split(' ')
		command = args[0][1:]

	args = args[1:]

	args = [ x for x in args if x ]

	if command in [ 'h', 'help' ]:
		await cmd_help(author, channel, args)

	elif command in [ 'al', 'alias' ]:
		await cmd_alias(author, channel, args)

	elif command in [ 'm', 'mods' ]:
		await cmd_mods(author, channel, args)

	elif command in [ 'a', 'arena' ]:
		await cmd_arena(author, channel, args)

	elif command in [ 'f', 'fa', 'fleet-arena' ]:
		await cmd_fleet_arena(author, channel, args)

	elif command in [ 'n', 'needed' ]:
		await cmd_mods_needed(author, channel, args)

	elif command in [ 'r', 'recos' ]:
		await cmd_mods_recommendations(author, channel, args)

	elif command in [ 's', 'stats' ]:
		await cmd_stats(author, channel, args)

	elif command in [ 'sh', 'sheets' ]:
		await cmd_sheets(author, channel, args)

	elif command in [ 're', 'restart' ]:
		await cmd_restart(author, channel, args)

	elif command in [ 're', 'restart' ]:
		await cmd_restart(author, channel, args)

	elif command in [ 'u', 'update' ]:
		await cmd_update(author, channel, args)

	else:
		msg = {
			'title': 'Unknown command',
			'color': 'red',
			'description': 'No such command: %s' % command,
		}

		await send_embed(channel, msg)

load_config()

ALLIES_DB = parse_allies_db()
AVATARS_DB = parse_avatars()
RECOS_DB = parse_recommendations()

bot.run(ipd_config['token'])
bot.close()
