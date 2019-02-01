#!/usr/bin/python3

import os, json, requests, socket

from utils import *
from constants import *

BASE_URL = 'https://swgoh.gg/api'

COMBAT_TYPE_UNIT = 1
COMBAT_TYPE_SHIP = 2

db = {}

DEFAULT_UNITS_DB = 'cache/units.json'
DEFAULT_SHIPS_DB = 'cache/ships.json'

def parse_units_or_ships(units):

	db = {}

	for unit in units:
		base_id = unit['base_id']
		db[base_id] = unit

	return db

def get_all_units_or_ships(db_file, url):

	try:
		response = requests.get(url)
		units = response.json()

		ensure_parents(db_file)

		fout = open(db_file, 'w+')
		fout.write(json.dumps(units))
		fout.close()

		return parse_units_or_ships(units)

	except:
		return None

def get_all_units():

	if 'units' in db:
		return db['units']

	url = '%s/characters/' % BASE_URL
	db['units'] = get_all_units_or_ships(DEFAULT_UNITS_DB, url)
	if not db['units']:
		fin = open(DEFAULT_UNITS_DB, 'r')
		data = fin.read()
		fin.close()
		db['units'] = parse_units_or_ships(json.loads(data))

	return db['units']

def get_all_ships():

	if 'ships' in db:
		return db['ships']

	url = '%s/ships/' % BASE_URL
	db['ships'] = get_all_units_or_ships(DEFAULT_SHIPS_DB, url)
	if not db['ships']:
		fin = open(DEFAULT_SHIPS_DB, 'r')
		data = fin.read()
		fin.close()
		db['ships'] = parse_units_or_ships(json.loads(data))

	return db['ships']

def get_avatar_url(base_id):

	units = get_all_units()

	image_url = units[base_id]['image']
	if image_url.startswith('//'):
		image_url = image_url.replace('//', '')

	if not image_url.startswith('https://'):
		image_url = 'https://%s' % image_url

	units[base_id]['image'] = image_url
	return image_url

def get_full_avatar_url(ally_code, base_id):

	units = get_all_units()
	unit = units[base_id]
	image_name = os.path.basename(unit['image'])
	unit = get_my_unit_by_id(ally_code, base_id)

	level = 'level' in unit and unit['level'] or 1
	gear = 'gear_level' in unit and unit['gear_level'] or 1
	stars = 'rarity' in unit and unit['rarity'] or 0
	zetas = 'zeta_abilities' in unit and len(unit['zeta_abilities']) or 0

	return 'http://%s/avatar/%s?level=%s&gear=%s&rarity=%s&zetas=%s' % (socket.gethostname(), image_name, level, gear, stars, zetas)

def get_my_units_and_ships(ally_code):

	if ally_code in db:
		return db[ally_code]

	db[ally_code] = {
		'units': {},
		'ships': {},
	}

	url = '%s/player/%s/' % (BASE_URL, ally_code)
	response = requests.get(url)
	jsondata = response.json()

	db[ally_code].update(jsondata['data'])

	for unit in jsondata['units']:
		unit = unit['data']
		base_id = unit['base_id']
		if unit['combat_type'] == COMBAT_TYPE_UNIT:
			unit['mods'] = {}
			unit['modsets'] = {}
			db[ally_code]['units'][base_id] = unit
		elif unit['combat_type'] == COMBAT_TYPE_SHIP:
			db[ally_code]['ships'][base_id] = unit
		else:
			raise Exception("Invalid combat_type: %s" % unit['combat_type'])

	return db[ally_code]

def get_my_mods(ally_code):

	if ally_code in db and 'mods-count' in db[ally_code]:
		return db[ally_code]
	else:
		get_my_units_and_ships(ally_code)

	url = '%s/players/%s/mods/' % (BASE_URL, ally_code)
	response = requests.get(url)
	all_mods = response.json()

	db[ally_code]['mods'] = all_mods['mods']
	db[ally_code]['mods-slots'] = {}
	db[ally_code]['mods-count'] = all_mods['count']

	stats = {}
	for mod in all_mods['mods']:
		slot = mod['slot']
		modset = mod['set']
		base_id = mod['character']
		unit = db[ally_code]['units'][base_id]
		unit['mods'][slot] = mod
		if modset not in unit['modsets']:
			unit['modsets'][modset] = 0

		if slot not in db[ally_code]['mods-slots']:
			db[ally_code]['mods-slots'][slot] = 0

		db[ally_code]['mods-slots'][slot] += 1
		unit['modsets'][modset] += 1

		if slot not in stats:
			stats[slot] = {}

		primary = mod['primary_stat']['name']
		if primary not in stats[slot]:
			stats[slot][primary] = 0

		stats[slot][primary] += 1

	db[ally_code]['mod-stats'] = stats

	for base_id, unit in db[ally_code]['units'].items():

		new_modsets = []
		unit['incomplete-modsets'] = False
		for modset_index, count, in unit['modsets'].items():
			modset_name = MODSETS[modset_index]
			complete_modset = MODSETS_NEEDED[modset_index]
			div, remain = divmod(count, complete_modset)
			if remain > 0:
				unit['incomplete-modsets'] = True
			for i in range(0, div):
				new_modsets.append(modset_name)

		unit['modsets'] = sorted(new_modsets) + [ '' ] * (3 - len(new_modsets))

		unit['missing-mods'] = []
		for i in range(1, 7):
			if i not in unit['mods']:
				modslot = MODSLOTS[ i ]
				unit['missing-mods'].append(modslot)

		unit['no-mods'] = len(unit['missing-mods']) == 6

	return db[ally_code]

def get_mod_stats(ally_code):

	if ally_code not in db or 'mod-stats' not in db[ally_code]:
		get_my_mods(ally_code)

	ally_db = db[ally_code]

	return ally_db['mod-stats']

def get_mods_count(ally_code):

	if ally_code not in db:
		get_my_units_and_ships(ally_code)

	ally_db = db[ally_code]

	return ally_db['mods-count']

def get_my_unit_by_id(ally_code, base_id):

	if ally_code not in db:
		get_my_mods(ally_code)

	ally_db = db[ally_code]

	if base_id in ally_db['units']:
		return ally_db['units'][base_id]

	return db['units'][base_id]

def get_my_ship_by_id(ally_code, base_id):

	if ally_code not in db:
		get_my_mods(ally_code)

	ally_db = db[ally_code]

	if base_id in ally_db['ships']:
		return ally_db['ships'][base_id]

	return None

def get_swgoh_profile_url(ally_code):

	url = 'https://swgoh.gg/p/%s/' % ally_code
	try:
		response = requests.head(url)
		if response.status_code == 200:
			return url
	except:
		pass

	return 'No profile found on swgoh.gg'

def get_arena_team(ally_code, fmt):

	if ally_code not in db:
		get_my_units_and_ships(ally_code)

	ally_db = db[ally_code]

	leader = ally_db['arena']['leader']
	members = ally_db['arena']['members']

	team = []

	for base_id in members:
		unit = ally_db['units'][base_id]

		fmt_cpy = str(fmt)
		fmt_cpy = format_char_details(unit, fmt_cpy)
		fmt_cpy = format_char_stats(unit, fmt_cpy)

		leader_str = ''
		if base_id == leader:
			leader_str = ' (Leader)'

		fmt_cpy = fmt_cpy.replace('%leader', leader_str).replace('%reinforcement', '')

		team.append(fmt_cpy)

	return team

def get_fleet_team(ally_code, fmt):

	if ally_code not in db:
		get_my_units_and_ships(ally_code)

	ally_db = db[ally_code]

	leader = ally_db['fleet_arena']['leader']
	members = ally_db['fleet_arena']['members']
	reinforcements = ally_db['fleet_arena']['reinforcements']

	team = []

	for base_id in members + reinforcements:
		unit = ally_db['ships'][base_id]

		fmt_cpy = str(fmt)
		fmt_cpy = format_char_details(unit, fmt_cpy)
		fmt_cpy = format_char_stats(unit, fmt_cpy)

		leader_str = ''
		if base_id == leader:
			leader_str = ' (Capital Ship)'

		reinforcement_str = ''
		if base_id in reinforcements:
			reinforcement_str = ' (Reinforcement)'


		fmt_cpy = fmt_cpy.replace('%leader', leader_str).replace('%reinforcement', reinforcement_str)

		team.append(fmt_cpy)

	return team

def get_player_name(ally_code):

	if ally_code not in db:
		get_my_units_and_ships(ally_code)

	ally_db = db[ally_code]

	return ally_db['name']

def get_arena_rank(ally_code):

	if ally_code not in db:
		get_my_units_and_ships(ally_code)

	ally_db = db[ally_code]

	return ally_db['arena']['rank']

def get_fleet_rank(ally_code):

	if ally_code not in db:
		get_my_units_and_ships(ally_code)

	ally_db = db[ally_code]

	return ally_db['fleet_arena']['rank']

def get_units_with_missing_mods(ally_code):

	if ally_code not in db or 'mods-count' not in db[ally_code]:
		get_my_mods(ally_code)

	ally_db = db[ally_code]

	matching_units = []
	for base_id, unit in ally_db['units'].items():
		if len(unit['missing-mods']) > 0 and unit['no-mods'] is False:
			matching_units.append(unit)

	return matching_units

def get_units_with_no_mods(ally_code):

	if ally_code not in db or 'mods-count' not in db[ally_code]:
		get_my_mods(ally_code)

	ally_db = db[ally_code]

	matching_units = []
	for base_id, unit in ally_db['units'].items():
		if unit['no-mods'] is True and unit['level'] >= 50:
			matching_units.append(unit)

	return matching_units

def get_units_with_incomplete_modsets(ally_code):

	if ally_code not in db or 'mods-count' not in db[ally_code]:
		get_my_mods(ally_code)

	ally_db = db[ally_code]

	matching_units = []
	for base_id, unit in ally_db['units'].items():
		if unit['incomplete-modsets'] is True and unit['no-mods'] is False:
			matching_units.append(unit)

	return matching_units
