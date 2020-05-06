import sys
import json
import traceback

from utils import http_post, get_ships_crew

CRINOLO_URLS = [
	'http://localhost:8081/api',
	'https://swgoh-stat-calc.glitch.me/api',
]

def add_pilots(players, units):

	pilots = []

	if not units:
		return pilots

	# Add pilots of requested ships if missing
	crews = get_ships_crew()
	base_ids = [ unit.base_id for unit in units ]
	for ship_id in list(base_ids):
		if ship_id in crews:
			for pilot in crews[ship_id]:
				if pilot not in base_ids:
					base_ids.append(pilot)
					pilots.append(pilot)

	# Remove units not requested
	for player in players:
		new_roster = []
		for unit in list(player['roster']):
			if unit['defId'] in base_ids:
				player['roster'].remove(unit)

	return pilots

def remove_pilots(players, pilots):

	# Remove added pilots
	for player in players:
		ally_code = player['allyCode']
		for unit in list(player['roster']):
			base_id = unit['defId']
			if base_id in pilots:
				player['roster'].remove(unit)

async def api_crinolo(players, units=[]):

	pilots = add_pilots(players, units)

	for crinolo_url in CRINOLO_URLS:

		url = '%s?flags=gameStyle&calcGP' % crinolo_url

		try:
			data, error = await http_post(url, json=players)

		except Exception as err:
			print(err)
			print(traceback.format_exc())
			print('ERROR: While posting to URL: %s' % url, file=sys.stderr)
			continue

		if error:
			raise Exception('http_post(%s) failed: %s' % (url, error))

		if 'error' in data:
			error = SwgohHelpException()
			error.title = 'Error from Crinolo API'
			error.data = data;
			raise error

		remove_pilots(players, pilots)
		return players

	return None
