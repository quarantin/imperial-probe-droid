from utils import get_units_dict, http_post

import json
import sys
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
#CRINOLO_PROD_URL = 'http://localhost:8080/statCalc/api'
CRINOLO_PROD_URL = 'https://swgoh-stat-calc.glitch.me/api'
CRINOLO_TEST_URL = 'https://crinolo-swgoh.glitch.me/testCalc/api'
CRINOLO_BETA_URL = 'https://crinolo-swgoh-beta.glitch.me/statCalc/api'

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

async def fetch_players(config, project):

	if type(project) is list:
		project = { 'allycodes': project }

	players = await api_swgoh_players(config, project)

	return sort_players(players)

async def fetch_guilds(config, project):

	if type(project) is list:
		project = { 'allycodes': project }

	ally_codes = project['allycodes']
	guilds = await api_swgoh_guilds(config, project)

	result = {}
	for guild in guilds:

		guild['roster'] = get_units_dict(guild['roster'], 'allyCode')
		for ally_code in ally_codes:
			if ally_code in guild['roster']:
				result[ally_code] = guild

	return result

async def fetch_crinolo_stats(config, project, players=None):

	if type(project) is list:
		project = { 'allycodes': project }

	if not players:
		players = await api_swgoh_players(config, project)

	stats = await api_crinolo(config, players)

	result = {}
	for player in stats:
		ally_code = player['allyCode']
		result[ally_code] = {}
		for unit in player['roster']:
			base_id = unit['defId']
			if base_id not in result[ally_code]:
				result[ally_code][base_id] = unit

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
