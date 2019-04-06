#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from utils import expired, get_dict_by_index, parse_modsets
from swgohgg import get_char_list

REAL_NAMES = {
	'Ahsoka Tano Fulcrum': 'Ahsoka Tano (Fulcrum)',
	'Bastila Shan Fallen': 'Bastila Shan (Fallen)',
	'\'CC-2224 Cody\'': 'CC-2224 "Cody"',
	'\'CT-21-0408 Echo\'': 'CT-21-0408 "Echo"',
	'\'CT-5555 Fives\'': 'CT-5555 "Fives"',
	'\'CT-7567 Rex\'': 'CT-7567 "Rex"',
	'Chirrut Imwe': 'Chirrut Îmwe',
	'Clone Sergeant P1': 'Clone Sergeant - Phase I',
	'\'Garazeb Zeb Orrelios\'': 'Garazeb "Zeb" Orrelios',
	'Kylo Ren Unmasked': 'Kylo Ren (Unmasked)',
	'Luke Skywalker Farmboy': 'Luke Skywalker (Farmboy)',
	'Obi-Wan Kenobi Old Ben': 'Obi-Wan Kenobi (Old Ben)',
	'Poggle The Lesser': 'Poggle the Lesser',
	'Rey Scavenger': 'Rey (Scavenger)',
	'Rey Jedi Training': 'Rey (Jedi Training)',
	'Qi\'Ra': 'Qi\'ra',
}

INFO_NAMES = {
	'B2 Super Battle Droid': 'B2',
	'Chirrut Îmwe': 'Chirrut Imwe',
	'Clone Sergeant - Phase I': 'Clone Sergeant P1',
}

VALID_STATS = [
	'Accuracy',
	'Defense',
	'Health',
	'Critical Avoidance',
	'Critical Chance',
	'Critical Damage',
	'Offense',
	'Potency',
	'Protection',
	'Speed',
	'Tenacity',
]

TRANSLATE_STATS = {
	'': '',
	'CC': 'Critical Chance',
	'CD': 'Critical Damage',
	'DEF': 'Defense',
	'HP': 'Health',
	'OFF': 'Offense',
	'POT': 'Potency',
	'SPE': 'Speed',
	'TEN': 'Tenacity',
}


FIX_STATS = {
	'Crit. Chance': [ 'Critical Chance' ],
	'Crit. Damage': [ 'Critical Damage' ],
}

db = {}

timeout = timedelta(hours=1)

def split_stats(stat):

	res = []
	stats = stat.split(' / ')
	for stat in stats:
		stat = stat.strip()
		if stat in FIX_STATS:
			stat = FIX_STATS[stat]

		if type(stat) is str:
			res.append(stat)
		else:
			res.extend(stat)

	for stat in res:
		if stat not in VALID_STATS:
			raise Exception('Invalid stat: %s' % stat)

	return res

def fetch_crouching_rancor_recos(recos=[]):

	if 'cr' in db and 'cr-expire' in db and not expired(db['cr-expire']):
		return db['cr']

	url = 'http://apps.crouchingrancor.com/mods/advisor.json'

	response = requests.get(url)
	data = response.json()

	chars = get_char_list(index='name')

	for reco in data['data']:

		info = reco['name'].strip("'")
		name = reco['cname']

		real_name = name
		if real_name in REAL_NAMES:
			real_name = REAL_NAMES[name]

		if real_name not in chars:
			raise Exception('Missing name `%s` from DB' % real_name)

		base_id = chars[ real_name ]['base_id']

		info_name = name
		if info_name in INFO_NAMES:
			info_name = INFO_NAMES[info_name]

		if info.startswith(name):
			info = info.replace(name, '').strip()

		elif info.startswith(info_name):
			info = info.replace(info_name, '').strip()

		elif info.startswith(info_name.strip("'")):
			info = info.replace(info_name.strip("'"), '').strip()

		else:
			raise Exception('Info does not start with char name for %s / %s / %s / %s' % (real_name, name, info_name, info))

		if real_name not in chars:
			raise Exception('Missing %s from DB' % real_name)

		if info and info[0] != 'z':
			info = info[0].upper() + info[1:]

		set1 = TRANSLATE_STATS[ reco['set1'] ]
		set2 = TRANSLATE_STATS[ reco['set2'] ]
		set3 = TRANSLATE_STATS[ reco['set3'] ]

		square_list   = split_stats(reco['square'])
		arrow_list    = split_stats(reco['arrow'])
		diamond_list  = split_stats(reco['diamond'])
		triangle_list = split_stats(reco['triangle'])
		circle_list   = split_stats(reco['circle'])
		cross_list    = split_stats(reco['cross'])

		for square in square_list:
			for arrow in arrow_list:
				for diamond in diamond_list:
					for triangle in triangle_list:
						for circle in circle_list:
							for cross in cross_list:

								recos.append({
									'source': 'Crouching Rancor',
									'base_id': base_id,
									'name': real_name,
									'set1': set1,
									'set2': set2,
									'set3': set3,
									'square': square,
									'arrow': arrow,
									'diamond': diamond,
									'triangle': triangle,
									'circle': circle,
									'cross': cross,
									'info': info,
								})

	db['cr'] = recos
	db['cr-expire'] = datetime.now() + timeout
	return recos

def fetch_swgohgg_meta_recos(recos=[], rank=1):

	if rank not in [ 1, 10, 100 ]:
		rank = 1

	key = 'gg-%d' % rank
	expire = 'gg-expire-%d'

	if key in db and expire in db and not expired(db[expire]):
		return db[key]

	char_list = get_char_list(index='name')
	url = 'https://swgoh.gg/mod-meta-report/rank_%d/' % rank
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'lxml')
	trs = soup.select('li tr')

	for tr in trs:

		tds = tr.find_all('td')
		if not tds:
			continue

		char_name = tds[0].text.strip()
		base_id = char_list[char_name]['base_id']
		modsets = parse_modsets(tds[1])
		prim_ar = tds[2].text.strip().split('/')
		prim_tr = tds[3].text.strip().split('/')
		prim_ci = tds[4].text.strip().split('/')
		prim_cr = tds[5].text.strip().split('/')

		for _ar in prim_ar:
			for _tr in prim_tr:
				for _ci in prim_ci:
					for _cr in prim_cr:
						recos.append({
							'source': 'swgoh.gg',
							'base_id': base_id,
							'name': char_name,
							'set1': modsets[0],
							'set2': modsets[1],
							'set3': modsets[2],
							'square': 'Offense',
							'arrow': _ar.strip(),
							'diamond': 'Defense',
							'triangle': _tr.strip(),
							'circle': _ci.strip(),
							'cross': _cr.strip(),
							'info': 'Meta Report',
						})

	db[key] = recos
	db[expire] = datetime.now() + timeout
	return recos

def fetch_capital_games_recos(recos=[]):

	if 'cg' in db and 'cg-expire' in db and not expired(db['cg-expire']):
		return db['cg']

	filename = 'cache/recos-capital-games.json'

	fin = open(filename, 'r')
	data = fin.read()
	fin.close()

	recos.extend(json.loads(data))

	db['cg'] = recos
	db['cg-expire'] = datetime.now() + timeout
	return recos

def fetch_all_recos(index='base_id', index2=None):

	recos_cg = fetch_capital_games_recos()
	recos_cr = fetch_crouching_rancor_recos()
	recos_gg = fetch_swgohgg_meta_recos()

	result = get_dict_by_index(recos_cg + recos_cr + recos_gg, index)

	if index2 is not None:
		for key in list(result):
			result[key] = get_dict_by_index(result[key], index2)

	return result

#test = fetch_all_recos(index='name', index2=None)
#print(json.dumps(test, indent=4))
