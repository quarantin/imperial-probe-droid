from utils import get_units_dict, http_post

import sys
import json
from datetime import datetime, timedelta

db = {
	'stats':   {},
	'players': {},
	'guilds':  {},
	'roster':  {},
	'units':   {},
	'events':  {},
	'zetas':   {},
	'data':    {},
}

SWGOH_HELP = 'https://api.swgoh.help'

DEFAULT_TIMEOUT_SECONDS = 3600

CRINOLO_URLS = [
	'http://localhost:8081/api',
	'https://swgoh-stat-calc.glitch.me/api',
]

#
# Internal - Do not call yourself
#

class SwgohHelpException(Exception):
	pass

async def get_access_token(config):

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
	data, error = await http_post(auth_url, headers=headers, data=data)
	if error:
		raise Exception('Authentication failed to swgoh.help API: %s' % error)

	if 'access_token' not in data:
		raise Exception('Authentication failed: Server returned `%s`' % data)

	config['swgoh.help']['access_token'] = data['access_token']
	config['swgoh.help']['access_token_expire'] = datetime.now() + timedelta(seconds=data['expires_in'])

	if 'debug' in config and config['debug'] is True:
		print('Logged in successfully', file=sys.stderr)

	return config['swgoh.help']['access_token']

async def get_headers(config):
	return {
		'method': 'post',
		'content-type': 'application/json',
		'authorization': 'Bearer %s' % await get_access_token(config),
	}

async def call_api(config, project, url):
	headers = await get_headers(config)

	if 'debug' in config and config['debug'] is True:
		print("CALL API: %s %s" % (url, project), file=sys.stderr)

	data, error = await http_post(url, headers=headers, json=project)
	if error:
		raise Exception('http_post(%s) failed: %s' % (url, error))

	if 'error' in data:
		error = SwgohHelpException()
		error.title = 'Error from swgoh.help API'
		error.data = data
		raise error

	return data

#
# API
#

async def api_swgoh_players(config, project, force=True):

	result = []
	expected_players = len(project['allycodes'])

	new_proj = dict(project)
	new_proj['allycodes'] = list(project['allycodes'])

	while len(result) < expected_players:

		returned = await call_api(config, new_proj, '%s/swgoh/players' % SWGOH_HELP)
		for player in returned:
			result.append(player)
			new_proj['allycodes'].remove(player['allyCode'])

		if force is False:
			break

	return result

async def api_swgoh_guilds(config, project):
	return await call_api(config, project, '%s/swgoh/guilds' % SWGOH_HELP)

async def api_swgoh_roster(config, project):
	return await call_api(config, project, '%s/swgoh/roster' % SWGOH_HELP)

async def api_swgoh_units(config, project):
	return await call_api(config, project, '%s/swgoh/units' % SWGOH_HELP)

async def api_swgoh_zetas(config, project):
	return await call_api(config, project, '%s/swgoh/zetas' % SWGOH_HELP)

async def api_swgoh_squads(config, project):
	return await call_api(config, project, '%s/swgoh/squads' % SWGOH_HELP)

async def api_swgoh_events(config, project):
	return await call_api(config, project, '%s/swgoh/events' % SWGOH_HELP)

async def api_swgoh_data(config, project):
	return await call_api(config, project, '%s/swgoh/data' % SWGOH_HELP)

async def api_crinolo(config, units):

	for crinolo_url in CRINOLO_URLS:

		url = '%s?flags=gameStyle,calcGP' % crinolo_url

		if 'debug' in config and config['debug'] is True:
			print('CALL CRINOLO API: %s' % url, file=sys.stderr)

		try:
			data, error = await http_post(url, json=units)

		except:
			print('ERROR: While posting to URL: %s' % url, file=sys.stderr)
			continue

		if error:
			raise Exception('http_post(%s) failed: %s' % (url, error))

		if 'error' in data:
			error = SwgohHelpException()
			error.title = 'Error from Crinolo API'
			error.data = data
			raise error

		return data

	return None

#
# Fetch functions
#

def sort_players(players):

	result = {}
	for player in players:

		if 'roster' in player:
			player['roster'] = get_units_dict(player['roster'], 'defId')

		ally_code = player['allyCode']
		result[ally_code] = player

	return result

def redis_get_players(config, ally_codes):

	players = []

	remain = list(ally_codes)
	for ally_code in ally_codes:
		player_key = 'player|%s' % ally_code
		#print('Checking cache for player: %s' % ally_code)
		data = config.redis.get(player_key)
		if data:
			#print('Found player in cache: %s' % ally_code)
			remain.remove(ally_code)
			players.append(json.loads(data.decode('utf-8')))

	return players, remain

def redis_set_players(config, players):

	for player in players:
		key = 'player|%s' % player['allyCode']
		expire = timedelta(seconds=DEFAULT_TIMEOUT_SECONDS)
		config.redis.setex(key, expire, json.dumps(player))

async def fetch_players(config, project):

	cache_result = False
	if type(project) is list:
		cache_result = True
		project = { 'allycodes': project }

	players, remain = redis_get_players(config, project['allycodes'])
	if not players or remain:
		project['allycodes'] = remain
		other_players = await api_swgoh_players(config, project)
		players.extend(other_players)
		if cache_result is True:
			redis_set_players(config, other_players)

	return sort_players(players)

def redis_get_guilds(config, ally_codes):

	guilds = []

	remain = list(ally_codes)
	for ally_code in ally_codes:
		player_key = 'player|%s' % ally_code
		player = config.redis.get(player_key)
		if player:
			player = json.loads(player.decode('utf-8'))
			key = 'guild|%s' % player['guildRefId']
			result = config.redis.get(key)
			if result:
				print('Found guild in cache! %s' % key)
				remain.remove(ally_code)
				guilds.append(json.loads(result.decode('utf-8')))

	return guilds, remain

def redis_set_guilds(config, guilds):

	for guild in guilds:

		for member in guild['roster']:

			key = 'player|%s' % member['allyCode']
			player = config.redis.get(key)
			if player:
				player = json.loads(player.decode('utf-8'))
				key = 'guild|%s' % player['guildRefId']
				expire = timedelta(seconds=DEFAULT_TIMEOUT_SECONDS)
				config.redis.setex(key, expire, json.dumps(guild))
				break

async def fetch_guilds(config, project):

	cache_result = False
	if type(project) is list:
		cache_result = True
		project = { 'allycodes': project }

	ally_codes = project['allycodes']
	guilds, remain = redis_get_guilds(config, ally_codes)
	if not guilds or remain:
		project['allycodes'] = remain
		other_guilds = await api_swgoh_guilds(config, project)
		guilds.extend(other_guilds)
		if cache_result is True:
			redis_set_guilds(config, other_guilds)

	result = {}
	for guild in guilds:

		guild['roster'] = get_units_dict(guild['roster'], 'allyCode')
		for ally_code in ally_codes:
			if ally_code in guild['roster']:
				result[ally_code] = guild

	return result

async def fetch_crinolo_stats(config, project, players=None, units=None):

	import DJANGO
	from swgoh.models import BaseUnitSkill

	all_zetas = list(BaseUnitSkill.objects.filter(is_zeta=1))
	db = {}
	for zeta in all_zetas:
		db[zeta.skill_id] = True

	cache_result = False
	if type(project) is list:
		cache_result = True
		project = { 'allycodes': project }

	if not players:

		players, remain = redis_get_players(config, project['allycodes'])
		if not players or remain:
			project['allycodes'] = remain
			other_players = await api_swgoh_players(config, project)
			players.extend(other_players)
			if cache_result is True:
				redis_set_players(config, other_players)

	to_remove = []
	if units is not None:

		crews = get_ships_crew()
		base_ids = [ unit.base_id for unit in units ]
		for ship_id in list(base_ids):
			if ship_id in crews:
				for pilot in crews[ship_id]:
					if pilot not in base_ids:
						base_ids.append(pilot)
						to_remove.append(pilot)

		for player in players:
			new_roster = []
			for unit in player['roster']:
				if unit['defId'] in base_ids:
					new_roster.append(unit)
			player['roster'] = new_roster

	stats = await api_crinolo(config, players)

	result = {}
	for player in stats:
		ally_code = player['allyCode']
		result[ally_code] = {}
		for unit in player['roster']:

			base_id = unit['defId']
			if base_id not in result[ally_code] and base_id not in to_remove:
				result[ally_code][base_id] = unit

			for skill in unit['skills']:
				#print(json.dumps(skill, indent=4))
				if skill['id'] in db:
					skill['isZeta'] = True

	for player in players:
		for unit in player['roster']:
			for skill in unit['skills']:
				if skill['id'] in db:
					skill['isZeta'] = True

	return result, players

#
# Localized functions
#

def get_unit_name(base_id, language):

	import DJANGO
	from swgoh.models import Translation

	try:
		t = Translation.objects.get(string_id=base_id, language=language)
		return t.translation

	except Translation.DoesNotExist:
		pass

	print('No character name found for base id: %s' % base_id, file=sys.stderr)
	return None

def get_simple_unit_name(base_id):
	return get_unit_name(base_id, 'eng_us').lower().replace(' ', '-').replace('"', '').replace('(', '').replace(')', '').replace('î', 'i').replace('Î', 'i').replace("'", '')

def get_ability_name(skill_id, language):

	import DJANGO
	from swgoh.models import BaseUnitSkill, Translation

	try:
		skill = BaseUnitSkill.objects.get(skill_id=skill_id)
		try:
			t = Translation.objects.get(string_id=skill.ability_ref, language=language)
			return t.translation

		except Translation.DoesNotExist:
			print("Missing translation for string ID %s" % skill.ability_ref)

	except BaseUnitSkill.DoesNotExist:
		pass

	# TODO
	#print('No ability name found for skill id: %s' % skill_id, file=sys.stderr)
	return None

def get_ships_crew():

	fin = open('cache/characters.json', 'r')
	data = json.loads(fin.read())
	fin.close()

	ships = {}

	for item in data:
		base_id = item['base_id']
		ship = item['ship']
		if ship:
			if ship not in ships:
				ships[ship] = []

			ships[ship].append(base_id)

	return ships
