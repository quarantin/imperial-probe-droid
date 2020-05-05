import sys
import json
import traceback

from utils import http_post, get_ships_crew

CRINOLO_URLS = [
	'http://localhost:8081/api',
	#'https://swgoh-stat-calc.glitch.me/api',
]

async def api_crinolo(players, units=[]):

	for crinolo_url in CRINOLO_URLS:

		url = '%s?flags=gameStyle' % crinolo_url

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
			error.data = data
			raise error

		return data

	return None

async def fetch_crinolo_stats(players=[], units=[]):

	import DJANGO
	from swgoh.models import BaseUnitSkill

	all_zetas = list(BaseUnitSkill.objects.filter(is_zeta=1))
	db = {}
	for zeta in all_zetas:
		db[zeta.skill_id] = True

	# Remove units not requested
	to_remove = []
	if units:

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

	# Add zeta info to skills
	for player in players:
		for unit in player['roster']:
			for skill in unit['skills']:
				if skill['id'] in db:
					skill['isZeta'] = True

	stats = await api_crinolo(players)

	result = {}
	for player in stats:
		ally_code = player['allyCode']
		result[ally_code] = {}
		for unit in player['roster']:

			base_id = unit['defId']
			if base_id not in result[ally_code] and base_id not in to_remove:
				result[ally_code][base_id] = unit

			for skill in unit['skills']:
				if skill['id'] in db:
					skill['isZeta'] = True

	return result, players

