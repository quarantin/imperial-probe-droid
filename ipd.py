#!/usr/bin/python3

import sys
import json
import pytz
import errno
import discord
import datetime
import requests
import subprocess

SHEETS_ALIASES = {
	'a': 'allies',
	'r': 'recommendations',
}

ipd_config = {}

ipd_config_json = 'config.json'

BASE_URL = 'https://swgoh.gg/api'

ACTIONS = {
	'list-chars',
	'list-ships',
	'list-mods',
}

PERCENT_STATS = [
	'armor',
	'critical-damage',
	'physical-critical-chance',
	'potency',
	'resistance',
	'special-critical-chance',
	'tenacity',
]

MODSETS = {
	1: 'Health',
	2: 'Offense',
	3: 'Defense',
	4: 'Speed',
	5: 'Critical Chance',
	6: 'Critical Damage',
	7: 'Potency',
	8: 'Tenacity',
}

MODSLOTS = {
	1: 'Square',
	2: 'Arrow',
	3: 'Diamond',
	4: 'Triangle',
	5: 'Circle',
	6: 'Cross',
}

FORMAT_LUT = {
	'gear':  'gear_level',
	'id':    'base_id',
	'level': 'level',
	'name':  'name',
	'power': 'power',
	'stars': 'rarity',
}

STATS_LUT = {
	'health':                      '1',
	'strength':                    '2',
	'agility':                     '3',
	'tactics':                     '4',
	'speed':                       '5',
	'physical-damage':             '6',
	'special-damage':              '7',
	'armor':                       '8',
	'resistance':                  '9',
	'armor-penetration':           '10',
	'resistance-penetration':      '11',
	'dodge-chance':                '12',
	'deflection-chance':           '13',
	'physical-critical-chance':    '14',
	'special-critical-chance':     '15',
	'critical-damage':             '16',
	'potency':                     '17',
	'tenacity':                    '18',
	'health-steal':                '27',
	'protection':                  '28',
	'physical-accuracy':           '37',
	'special-accuracy':            '38',
	'physical-critical-avoidance': '39',
	'special-critical-avoidance':  '40',
}

COLORS = {
	'blue':       0x268bd2,
	'cyan':       0x2aa198,
	'dark-gray':  0x586e75,
	'green':      0x859900,
	'light-gray': 0x839496,
	'orange':     0xcb4b16,
	'red':        0xdc322f,
	'yellow':     0xb58900,
}

def now():
	tz = pytz.timezone(ipd_config['timezone'])
	return tz.localize(datetime.datetime.now())

def color(colour):

	if colour not in COLORS:
		raise Exception('Invalid color: %s' % colour)

	return discord.Colour(COLORS[colour])

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

	lines = response.text.split('\r\n')
	for line in lines:
		toks = line.split(',')
		content.append(toks[0:cols])

	return iter(content)

def parse_allies_db():

	url = ipd_config['sheets']['allies']

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

def find_unit_by_keyword(units, keyword):

	keyword = keyword.lower()

	for base_id, unit in units.items():

		name = unit['name'].lower()
		index = name.find(keyword)
		if index != -1:
			return unit

	return None

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

	if not timestamp:
		timestamp = now()

	embed = discord.Embed(title=msg['title'], colour=color(msg['color']), description=msg['description'], timestamp=timestamp)

	await bot.send_message(channel, embed=embed)

async def parse_ally_codes(author, channel, args):

	ally_codes = []

	for arg in args:

		if len(arg) >= 9 and arg.isdigit():
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

	return ally_codes

HELP_HELP = {
	'title': 'Imperial Probe Droid Help - Prefix: %prefix',
	'color': 'blue',
	'description': """------------------------------
**Botmaster(s)**: %authors
------------------------------
**Help commands**
**`help`**: This help menu
------------------------------
**Player commands**
**`arena`**: Show arena team for the supplied ally code.
**`fleet-arena`**: Show fleet arena team for the supplied ally code.
**`mods`**: Show stats about mods for the supplied ally code.
**`sheets`**: Show spreadsheets.
"""
}

HELP_ARENA = {
	'title': 'Player info',
	'color': 'blue',
	'description': """Shows arena team for the supplied ally codes.

**Syntax**
```
%prefixarena [ally codes] [l|s|v]
%prefixarena [ally codes] c <format>```

**Options**
lite (l): lite display
short (s): short display
verbose (v): verbose display
custom (c): custom display

**Aliases**
```
a```

**Format**
The custom format can contain the following keywords:
```
%name (character name)
%leader (leader of the group)
%level (level of the character)
%gear (level of gear of the character)
%power (power of the character)
%health (health of the character)
%speed (speed of the character)
...```
Also spaces need to be replaced with %20 and newlines with %0A.

**Example**
```
%prefixa
%prefixa l
%prefixa 123456789
%prefixa 123456789 234567891
%prefixa 123456789 lite
%prefixa c %speed%20%name```"""
}

HELP_FLEET_ARENA = {
	'title': 'Player info',
	'color': 'blue',
	'description': """Shows fleet arena team for the supplied ally codes.

**Options**
lite (l)
short (s)
verbose (v)
custom (c)

**Aliases**
```
f
fa```

**Example**
```
%prefixf
%prefixf 123456789
%prefixf 123456789 234567891
%prefixf 123456788 verbose
%prefixf c %speed%20%name```"""

}

HELP_MODS = {

}

HELP_SHEETS = {

}

HELP_MESSAGES = {
	'a': HELP_ARENA,
	'arena': HELP_ARENA,
	'f': HELP_FLEET_ARENA,
	'fa': HELP_FLEET_ARENA,
	'fleet-arena': HELP_FLEET_ARENA,
	'h': HELP_HELP,
	'help': HELP_HELP,
	'm': HELP_MODS,
	'mods': HELP_MODS,
	'sh': HELP_SHEETS,
	'sheets': HELP_SHEETS,
}

async def handle_help(author, channel, args):

	msg = HELP_HELP
	msg['title'] = msg['title'].replace('%prefix', ', '.join(ipd_config['prefix']))
	msg['description'] = msg['description'].replace('%authors', ', '.join(ipd_config['authors']))

	if args:
		command = args[0]
		if command in HELP_MESSAGES:
			msg = HELP_MESSAGES[command]

	await send_embed(channel, msg)

async def handle_arena(author, channel, args):

	fmt = fmt_short

	ally_codes = await parse_ally_codes(author, channel, args)
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

async def handle_fleet_arena(author, channel, args):

	fmt = fmt_short

	ally_codes = await parse_ally_codes(author, channel, args)
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

async def handle_mods(author, channel, args):

	action = ''

	ally_codes = await parse_ally_codes(author, channel, args)
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

		if action == 'stats':

			mods, stats = parse_mods(mods)

			output = '%s has the following equipped mods:\n' % player
			await bot.send_message(channel, output)

			for modset_id, modset_name in MODSETS.items():

				modset = mods[modset_name]

				output = '%s (%d)\n' % (modset_name, stats[modset_name])
				for modslot_name, modslot in modset.items():
					key = '%s-%s' % (modset_name, modslot_name)
					output = output + '\t%s (%d)\n' % (modslot_name, stats[key])
					for stat, count in modslot.items():

						line = '\t\t %s: %d\n' % (stat, count)
						output = output + line

				await bot.send_message(channel, output)

		elif action == 'missing':

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

async def handle_sheets(author, channel, args):

	sheets = {}
	for arg in args:

		if arg in SHEETS_ALIASES:
			arg = SHEETS_ALIASES[arg]

		if arg in ipd_config['sheets']:
			sheets[arg] = ipd_config['sheets'][arg]

	if not sheets:
		sheets = ipd_config['sheets']

	lines = []
	for name, url in sorted(sheets.items()):
		lines.append('**`%s`**: %s' % (name, url))

	msg = {
		'title': '',
		'color': 'blue',
		'description': '\n'.join(lines),
	}

	await send_embed(channel, msg)

async def handle_update(author, channel, args):

	if author not in ipd_config['admins']:

		print('%s is not an admin and therefore is not allowed to use update.' % author)

		msg = {
			'title': 'Unauthorized Command',
			'color': 'red',
			'description': 'You are not allowed to run this command because you are not an administrator.',
		}

		await send_embed(channel, msg)
		return

	"""
	TODO
	subprocess.call([ 'git', 'reset', '--hard'])
	subprocess.call([ 'git', 'fetch'])
	subprocess.call([ 'git', 'pull', 'origin', 'master'])
	"""
	bot.logout()
	bot.close()

	print('Updated!')
	sys.exit()

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
	json.dumps(ipd_config, indent=4, sort_keys=True)

bot = discord.Client()

@bot.event
async def on_ready():
	print('Logged in as %s (ID:%s, TOKEN:%s)' % (bot.user.name, bot.user.id, ipd_config['token']))
	print('\nTimezone: %s' % ipd_config['timezone'])

	print('\nAdmins:')
	for admin in ipd_config['admins']:
		print(' - %s' % admin)

	print('\nAliases:')
	for item in ipd_config['aliases'].items():
		print(' - %s: %s' % item)

	print('\nAuthors:')
	for author in ipd_config['authors']:
		print(' - %s' % author)

	print('\nSpreadsheets:')
	for item in ipd_config['sheets'].items():
		print(' - %s: %s' % item)

@bot.event
async def on_message(message):

	if not message.content.startswith(ipd_config['prefix']):
		return

	channel = message.channel
	nick = message.author.nick or message.author.id
	author = '@%s' % nick
	args = message.content.split(' ')
	command = args[0][1:]
	if command in ipd_config['aliases']:
		args = message.content.replace(command, ipd_config['aliases'][command]).split(' ')
		command = args[0][1:]

	args = args[1:]

	if command in [ 'h', 'help' ]:
		await handle_help(author, channel, args)

	elif command in [ 'm', 'mods' ]:
		await handle_mods(author, channel, args)

	elif command in [ 'a', 'arena' ]:
		await handle_arena(author, channel, args)

	elif command in [ 'f', 'fa', 'fleet-arena' ]:
		await handle_fleet_arena(author, channel, args)

	elif command in [ 'sh', 'sheets' ]:
		await handle_sheets(author, channel, args)

	elif command in [ 'u', 'update' ]:
		await handle_update(author, channel, args)

	else:
		msg = {
			'title': 'Unknown command',
			'color': 'red',
			'description': 'No such command: %s' % command,
		}

		await send_embed(channel, msg)

load_config()

ALLIES_DB = parse_allies_db()

print("TOKEN: %s" % ipd_config['token'])
bot.run(ipd_config['token'])
bot.close()
