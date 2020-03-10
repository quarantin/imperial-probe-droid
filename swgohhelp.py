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

#CRINOLO_PROD_URL = 'https://crinolo-swgoh.glitch.me/statCalc/api'
CRINOLO_PROD_URL = 'http://localhost:8081/api'
#CRINOLO_PROD_URL = 'https://swgoh-stat-calc.glitch.me/api'
#CRINOLO_TEST_URL = 'https://crinolo-swgoh.glitch.me/testCalc/api'
#CRINOLO_BETA_URL = 'https://crinolo-swgoh-beta.glitch.me/statCalc/api'

#
# Internal - Do not call yourself
#

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
	response, error = await http_post(auth_url, headers=headers, data=data)
	if error:
		raise Exception('Authentication failed to swgohhelp API: %s' % error)

	data = response.json()
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
		print("CALL API: %s %s %s" % (url, headers, project), file=sys.stderr)

	response, error = await http_post(url, headers=headers, json=project)
	if error:
		raise Exception('http_post(%s) failed: %s' % (url, error))

	try:
		data = response.json()

	except Exception as err:
		print("Failed to decode JSON:\n%s\n---" % response.content)
		raise err

	if 'error' in data and 'error_description' in data:
		raise Exception(data['error_description'])

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
	url = '%s?flags=gameStyle,calcGP' % CRINOLO_PROD_URL

	if 'debug' in config and config['debug'] is True:
		print('CALL CRINOLO API: %s' % url, file=sys.stderr)

	response, error = await http_post(url, json=units)
	if error:
		raise Exception('http_post(%s) failed: %s' % (url, error))

	#data = json.loads(response.decode('utf-8'))
	data = response.json()
	if 'error' in data:
		raise Exception('POST request failed for URL: %s\n%d Error: %s' % (url, response.status_code, data['error']))

	return data
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
		data = config['redis'].get(player_key)
		if data:
			#print('Found player in cache: %s' % ally_code)
			remain.remove(ally_code)
			players.append(json.loads(data.decode('utf-8')))

	return players, remain

async def fetch_players(config, project):

	if type(project) is list:
		project = { 'allycodes': project }

	players, remain = redis_get_players(config, project['allycodes'])
	if remain:
		project['allycodes'] = remain
		players.extend(await api_swgoh_players(config, project))

	return sort_players(players)

def redis_get_guilds(config, ally_codes):

	guilds = []

	ally_codes_cpy = list(ally_codes)
	for ally_code in ally_codes:
		player_key = 'player|%s' % ally_code
		player = config['redis'].get(player_key)
		if player:
			player = json.loads(player.decode('utf-8'))
			key = 'guild|%s' % player['guildRefId']
			result = config['redis'].get(key)
			if result:
				print('Found guild in cache! %s' % key)
				ally_codes_cpy.remove(ally_code)
				guilds.append(json.loads(result.decode('utf-8')))

	return guilds, ally_codes_cpy

async def fetch_guilds(config, project):

	if type(project) is list:
		project = { 'allycodes': project }

	ally_codes = project['allycodes']
	guilds, remain = redis_get_guilds(config, ally_codes)
	if remain:
		project['allycodes'] = remain
		guilds.extend(await api_swgoh_guilds(config, project))

	result = {}
	for guild in guilds:

		guild['roster'] = get_units_dict(guild['roster'], 'allyCode')
		for ally_code in ally_codes:
			if ally_code in guild['roster']:
				result[ally_code] = guild

	return result

async def fetch_crinolo_stats(config, project, players=None):

	import DJANGO
	from swgoh.models import BaseUnitSkill

	all_zetas = list(BaseUnitSkill.objects.filter(is_zeta=1))
	db = {}
	for zeta in all_zetas:
		db[zeta.skill_id] = True

	if type(project) is list:
		project = { 'allycodes': project }

	if not players:

		players, remain = redis_get_players(config, project['allycodes'])
		if remain:
			project['allycodes'] = remain
			players.extend(await api_swgoh_players(config, project))
		#players = await api_swgoh_players(config, project)

	stats = await api_crinolo(config, players)

	result = {}
	for player in stats:
		ally_code = player['allyCode']
		result[ally_code] = {}
		for unit in player['roster']:

			base_id = unit['defId']
			if base_id not in result[ally_code]:
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
