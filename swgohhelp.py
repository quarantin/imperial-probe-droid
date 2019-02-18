#!/usr/bin/python3

from utils import get_units_dict

import sys
import requests
from datetime import datetime, timedelta

db = {
	'guilds':  {},
	'players': {},
	'roster':  {},
	'units':   {},
	'events':  {},
	'zetas':   {},
	'data':    {},
}

SWGOH_HELP = 'https://api.swgoh.help'

CRINOLO_PROD_URL = 'https://crinolo-swgoh.glitch.me/statCalc/api/player'
CRINOLO_TEST_URL = 'https://crinolo-swgoh.glitch.me/testCalc/api/player'

#
# Internal - Do not call yourself
#

def get_access_token(config):

	if 'access_token' in config['swgoh.help']:
		expire = config['swgoh.help']['access_token_expire']
		if expire > datetime.now() + timedelta(seconds=60):
			return config['swgoh.help']['access_token']

	headers = {
		'method': 'post',
		'content-type': 'application/x-www-form-urlencoded',
	}

	data = {
		'username': config['swgoh.help']['username'],
		'password': config['swgoh.help']['password'],
		'grant_type': 'password',
		'client_id': 'abc',
		'client_secret': '123',
	}

	auth_url = '%s/auth/signin' % SWGOH_HELP
	response = requests.post(auth_url, headers=headers, data=data)
	data = response.json()

	if 'access_token' not in data:
		raise Exception('Authentication failed: Server returned `%s`' % data)

	config['swgoh.help']['access_token'] = data['access_token']
	config['swgoh.help']['access_token_expire'] = datetime.now() + timedelta(seconds=data['expires_in'])

	print('Logged in successfully', file=sys.stderr)
	return config['swgoh.help']['access_token']

def get_headers(config):
	return {
		'method': 'post',
		'content-type': 'application/json',
		'authorization': 'Bearer %s' % get_access_token(config),
	}

def call_api(config, project, url):
	print("CALL API: %s %s" % (url, project))
	return requests.post(url, headers=get_headers(config), json=project).json()

#
# API
#

def api_crinolo(config, rosters):
	url = '%s/characters' % CRINOLO_TEST_URL
	return requests.post(url, rosters).json()

def api_swgoh_players(config, project):
	return call_api(config, project, '%s/swgoh/players' % SWGOH_HELP)

def api_swgoh_guilds(config, project):
	return call_api(config, project, '%s/swgoh/guilds' % SWGOH_HELP)

def api_swgoh_roster(config, project):
	return call_api(config, project, '%s/swgoh/roster' % SWGOH_HELP)

def api_swgoh_units(config, project):
	return call_api(config, project, '%s/swgoh/units' % SWGOH_HELP)

def api_swgoh_zetas(config, project):
	return call_api(config, project, '%s/swgoh/zetas' % SWGOH_HELP)

def api_swgoh_squads(config, project):
	return call_api(config, project, '%s/swgoh/squads' % SWGOH_HELP)

def api_swgoh_events(config, project):
	return call_api(config, project, '%s/swgoh/events' % SWGOH_HELP)

def api_swgoh_data(config, project):
	return call_api(config, project, '%s/swgoh/data' % SWGOH_HELP)

#
# Fetch functions
#

def fetch_players(config, ally_codes, key='name'):

	# Remove ally codes for which we already have fetched the data
	needed = list(ally_codes)
	for ally_code in ally_codes:
		if int(ally_code) in db['players'] and key in db['players'][int(ally_code)]:
			needed.remove(ally_code)

	if needed:

		# Perform API call to retrieve newly needed player info
		players = api_swgoh_players(config, {
			'allycodes': needed,
		})

		# Store newly needed players in db
		for player in players:

			total, char, ship = get_player_gp_from_roster(player['roster'])

			player['gp'] = {
				'total': total,
				'char': char,
				'ship': ship,
			}

			player['roster'] = get_units_dict(player['roster'], 'defId')

			ally_code = player['allyCode']
			db['players'][ally_code] = player

	players = {}
	for ally_code in ally_codes:
		players[ally_code] = db['players'][int(ally_code)]

	return players

def fetch_guilds(config, ally_codes):

	# Remove ally codes for which we already have fetched the guild data
	needed = list(ally_codes)
	for ally_code in ally_codes:
		for guild_name, guild in db['guilds'].items():
			for player in guild['roster']:
				if int(ally_code) == player['allyCode']:
					needed.remove(ally_code)

	if needed:

		# Perform API call to retrieve newly needed guild info
		guilds = api_swgoh_guilds(config, {
			'allycodes': needed,
		})

		# Store newly needed guilds in db
		for guild in guilds:
			guild['roster'] = get_units_dict(guild['roster'], 'allyCode')
			guild_name = guild['name']
			db['guilds'][guild_name] = guild

	guilds = {}

	for guild_name, guild in db['guilds'].items():

		for ally_code in ally_codes:
			if ally_code in guild['roster']:
				guilds[guild_name] = guild

	return guilds

def fetch_units(config, ally_codes):

	# Remove ally codes for which we already have fetched the data
	needed = list(ally_codes)
	for ally_code in ally_codes:
		if int(ally_code) in db['units']:
			needed.remove(ally_code)

	if needed:

		# Perform API call to retrieve newly needed units info
		units = api_swgoh_units(config, {
			'allycodes': needed,
		})

		# Store newly needed units in db
		for base_id, units in units.items():
			for unit in units:
				ally_code = unit['allyCode']
				if ally_code not in db['units']:
					db['units'][ally_code] = {}

				db['units'][ally_code][base_id] = unit

	return db['units']

def fetch_roster(config, ally_codes):

	# Remove ally codes for which we already have fetched the data
	needed = list(ally_codes)
	for ally_code in ally_codes:
		if int(ally_code) in db['roster']:
			needed.remove(ally_code)

	if needed:

		# Perform API call to retrieve newly needed roster info
		rosters = api_swgoh_roster(config, {
			'allycodes': needed,
		})

		# Store newly needed rosters in db
		for roster in rosters:
			for base_id, unit_roster in roster.items():
				for unit in unit_roster:
					ally_code = unit['allyCode']
					if ally_code not in db['roster']:
						db['roster'][ally_code] = {}

					db['roster'][ally_code][base_id] = unit

	rosters = {}
	for ally_code in ally_codes:
		rosters[ally_code] = db['roster'][int(ally_code)]

	return rosters

# Stats helper from crinolo

def fetch_stats(config, ally_codes):

	# Perform API call to retrieve newly needed players info
	players = fetch_players(config, ally_codes)

	# Remove ally codes for which we already have fetched the data
	needed = list(ally_codes)
	for ally_code in ally_codes:
		if int(ally_code) in db['stats']:
			needed.remove(ally_code)

	if needed:

		stats = api_crinolo(config, [ player['roster'] for player in players ])
		for stat in stats:
			print(stat)

	return
#
# Utility functions
#

def get_guilds_ally_codes(guilds):

	ally_codes = {}

	for guild_name, guild in guilds.items():
		for ally in guild['roster']:
			ally_code = ally['allyCode']
			ally_codes[ally_code] = ally

	return ally_codes

def get_player_names(config, ally_codes):

	fetch_players(config, ally_codes, 'name')

	names = {}
	for ally_code in ally_codes:
		ally_code = int(ally_code)
		names[ally_code] = db['players'][ally_code]['name']

	return names

def get_player_name(config, ally_code):
	data = get_player_names(config, [ ally_code ])
	return data[int(ally_code)]

def get_last_syncs(config, ally_codes, date_format):

	fetch_players(config, ally_codes, 'updated')

	updated = {}
	for ally_code in ally_codes:
		ally_code = int(ally_code)
		updated[ally_code] = datetime.fromtimestamp(int(db['players'][ally_code]['updated']) / 1000).strftime(date_format)

	return updated

def get_last_sync(config, ally_code, date_format):
	data = get_last_syncs(config, [ ally_code ], date_format)
	return data[int(ally_code)]

def get_arena_ranks(config, ally_codes, arena_type):

	if arena_type not in [ 'char', 'ship' ]:
		raise Exception('Invalid arena type: %s. It must be either \'char\' or \'ship\'.' % arena_type)

	fetch_players(config, ally_codes, 'arena')

	ranks = {}
	for ally_code in ally_codes:
		ally_code = int(ally_code)
		ranks[ally_code] = db['players'][ally_code]['arena'][arena_type]['rank']

	return ranks

def get_arena_rank(config, ally_code, arena_type):
	data = get_arena_ranks(config, [ ally_code ], arena_type)
	return data[int(ally_code)]

def get_arena_squads(config, ally_codes, arena_type):

	if arena_type not in [ 'char', 'ship' ]:
		raise Exception('Invalid arena type: %s. It must be either \'char\' or \'ship\'.' % arena_type)

	fetch_players(config, ally_codes, 'arena')

	squads = {}
	for ally_code in ally_codes:
		ally_code = int(ally_code)
		squads[ally_code] = db['players'][ally_code]['arena'][arena_type]['squad']

	return squads

def get_arena_squad(config, ally_code, arena_type):
	data = get_arena_squads(config, [ ally_code ], arena_type)
	return data[int(ally_code)]

def get_player_gp_from_roster(roster):

	total, char, ship = 0, 0, 0

	for unit in roster:

		gp = unit['gp']

		total += gp

		if unit['combatType'] is 1:
			char += gp

		if unit['combatType'] is 2:
			ship += gp

	return total, char, ship

def get_stats(config, ally_code):

	stats = {}

	ally_code = int(ally_code)
	players = fetch_players(config, [ ally_code ])

	if 'char_stats' in players[ally_code]:
		return players[ally_code]['char_stats']

	url = '%s/%s/characters?flags=withModCalc' % (CRINOLO_TEST_URL, ally_code)
	roster = requests.get(url).json()
	for unit in roster:
		base_id = unit['defId']
		stats[base_id] = unit['stats']

	players[ally_code]['char_stats'] = stats
	return stats

def get_ability_name(config, skill_id, lang):

	name = 'Not found'
	if lang not in config['skills']:
		lang = 'en'

	if skill_id in config['skills'][lang]:
		ability_id = config['skills'][lang][skill_id]
		if ability_id in config['abilities'][lang]:
			name = config['abilities'][lang][ability_id]

	return name
