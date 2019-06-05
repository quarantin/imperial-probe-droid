from utils import get_units_dict, http_get, http_post

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

CRINOLO_PROD_URL = 'https://crinolo-swgoh.glitch.me/statCalc/api'
CRINOLO_TEST_URL = 'https://crinolo-swgoh.glitch.me/testCalc/api'
CRINOLO_BETA_URL = 'https://crinolo-swgoh-beta.glitch.me/statCalc/api'

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
	response, error = http_post(auth_url, headers=headers, data=data)
	if error:
		raise Exception('Authentication failed to swgohhelp API: %s' % error)

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
	headers = get_headers(config)
	print("CALL API: %s %s %s" % (url, headers, project), file=sys.stderr)
	response, error = http_post(url, headers=headers, json=project)
	if error:
		raise Exception('http_post(%s) failed: %s' % (url, error))

	data = response.json()
	if 'error' in data and 'error_description' in data:
		raise Exception(data['error_description'])

	return data

#
# API
#

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

def api_crinolo(config, units):
	url = '%s?flags=gameStyle' % CRINOLO_BETA_URL
	print('CALL CRINOLO API: %s' % url, file=sys.stderr)
	response, error = http_post(url, json=units)
	if error:
		raise Exception('http_post(%s) failed: %s' % (url, error))

	data = response.json()
	if 'error' in data:
		raise Exception('POST request failed for URL: %s\n%d Error: %s' % (url, response.status_code, data['error']))

	return data
#
# Fetch functions
#

def fetch_players(config, project):

	if type(project) is list:
		project = { 'allycodes': project }

	players = api_swgoh_players(config, project)

	result = {}
	for player in players:

		if 'roster' in player:
			player['roster'] = get_units_dict(player['roster'], 'defId')

		ally_code = player['allyCode']
		result[ally_code] = player

	return result

def fetch_guilds(config, project):

	if type(project) is list:
		project = { 'allycodes': project }

	ally_codes = project['allycodes']
	guilds = api_swgoh_guilds(config, project)

	result = {}
	for guild in guilds:

		guild['roster'] = get_units_dict(guild['roster'], 'allyCode')
		for ally_code in ally_codes:
			if ally_code in guild['roster']:
				result[ally_code] = guild

	return result

def fetch_crinolo_stats(config, project):

	if type(project) is list:
		project = { 'allycodes': project }

	players = api_swgoh_players(config, project)

	stats = api_crinolo(config, players)

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

def get_unit_name(config, base_id, language):

	import DJANGO
	from swgoh.models import Translation

	try:
		t = Translation.objects.get(string_id=base_id, language=language)
		return t.translation

	except Translation.DoesNotExist:
		pass

	print('No character name found for base id: %s' % base_id)
	return None

def get_ability_name(config, skill_id, language):

	import DJANGO
	from swgoh.models import Translation

	if skill_id in config['skills']:
		ability_id = config['skills'][skill_id]['abilityReference']
		try:
			t = Translation.objects.get(string_id=ability_id, language=language)
			return t.translation

		except Translation.DoesNotExist:
			pass

	print('No ability name found for skill id: %s' % skill_id)
	return None
