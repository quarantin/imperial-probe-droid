#!/usr/bin/python3

from utils import cache_expired, ensure_parents, get_units_dict, http_get, parse_modsets

from swgohhelp import fetch_players

import os
import json
import socket
from bs4 import BeautifulSoup

db = {}

SWGOH_GG_API_URL = 'https://swgoh.gg/api'

META_UNITS_URL = 'https://swgoh.gg/meta-report/'
META_SHIPS_URL = 'https://swgoh.gg/fleet-meta-report/'
META_MODS_URL = 'https://swgoh.gg/mod-meta-report/rank_10/'
META_ZETAS_URL = 'https://swgoh.gg/ability-report/'

def download_unit_list(key, url, index='base_id'):

	by_id = '%s-by-%s' % (key, index)
	key = '%s-%s' % (key, index)
	cache = 'cache/%s.json' % key
	ensure_parents(cache)

	if key in db:
		return db[by_id]

	elif os.path.exists(cache) and os.path.getsize(cache) > 0 and not cache_expired(cache):
		fin = open(cache, 'r')
		data = fin.read()
		fin.close()
		unit_list = json.loads(data)

	else:
		response, error = http_get(url)
		if error:
			raise Exception('http_get(%s) failed: %s' % (url, error))

		unit_list = response.json()

		fout = open(cache, 'w+')
		fout.write(json.dumps(unit_list))
		fout.close()

	db[key] = unit_list
	db[by_id] = get_units_dict(unit_list, index)
	return db[by_id]

def get_gear_list(index='base_id'):
	return download_unit_list('gear', '%s/gear/' % SWGOH_GG_API_URL, index=index)

def get_char_list(index='base_id'):
	return download_unit_list('chars', '%s/characters/' % SWGOH_GG_API_URL, index=index)

def get_ship_list(index='base_id'):
	return download_unit_list('ships', '%s/ships/' % SWGOH_GG_API_URL, index=index)

def get_unit_list(index='base_id'):
	units = get_char_list(index=index)
	units.update(get_ship_list(index=index))
	return units

def get_swgohgg_profile_url(ally_code):

	url = 'https://swgoh.gg/p/%s/' % ally_code

	try:
		response, error = http_get(url, headOnly=True)
		if not error and response.status_code == 200:
			return url
	except:
		pass

	return 'No profile found on swgoh.gg for ally code: %s' % ally_code

def get_avatar_url(base_id):

	chars = get_char_list()

	image_url = chars[base_id]['image']
	if image_url.startswith('//'):
		image_url = image_url.replace('//', '')

	if not image_url.startswith('https://'):
		image_url = 'https://%s' % image_url

	chars[base_id]['image'] = image_url
	return image_url

def get_full_avatar_url(config, image, unit):

	image = os.path.basename(image)

	level, gear, rarity, zetas = 1, 1, 0, 0

	if unit is not None:
		level  = 'level'     in unit and unit['level']      or 1
		gear   = 'gearLevel' in unit and unit['gearLevel']  or 1
		rarity = 'starLevel' in unit and unit['starLevel']  or 0
		zetas  = 'zetas'     in unit and len(unit['zetas']) or 0

		if 'gearLevel' not in unit and 'gear' in unit:
			gear = unit['gear']

		if 'starLevel' not in unit and 'rarity' in unit:
			rarity = unit['rarity']

	#return 'https://api.swgoh.help/image/char/%s?level=%s&gear=%s&rarity=%s&zetas=%s' % (base_id, level, gear, rarity, zetas)
	url = 'http://%s/avatar/%s?level=%s&gear=%s&rarity=%s&zetas=%s' % (config['server'], image, level, gear, rarity, zetas)
	return url

def get_full_ship_avatar_url(ally_code, base_id):
	#return 'https://api.swgoh.help/image/ship/%s?rarity=%s&level=%s&bg=36393E&pilots=DEATHTROOPER-7-85-12-null%7CSHORETROOPER-7-85-12-null' % (base_id),
	pass
#
# Meta Reports
#

def get_top_rank1_leaders(top_n, html_id, url):

	top_leaders = []

	response, error = http_get(url)
	if error:
		raise Exception('http_get(%s) failed: %s' % (url, error))

	soup = BeautifulSoup(response.text, 'lxml')
	trs = soup.select('li#%s tr' % html_id)

	i = 1
	for tr in trs:

		if i > top_n:
			break

		tds = tr.find_all('td')
		if not tds:
			continue

		unit = tds[0].text.strip()
		count = tds[1].text.strip()
		stat = tds[2].text.strip()

		top_leaders.append((unit, count, stat))

		i += 1

	return top_leaders

def get_top_rank1_squads(top_n, html_id, url):

	top_squads = []

	response, error = http_get(url)
	if error:
		raise Exception('http_get(%s) failed: %s' % (url, error))

	soup = BeautifulSoup(response.text, 'lxml')
	trs = soup.select('li#%s tr' % html_id)

	i = 1
	for tr in trs:

		if i > top_n:
			break

		tds = tr.find_all('td')
		if not tds:
			continue

		squad = tds[0]
		count = tds[1].text.strip()
		percent = tds[2].text.strip()

		imgs = squad.find_all('img', alt=True)
		squad = []
		for img in imgs:
			squad.append(img['alt'])

		top_squads.append((squad, count, percent))

		i += 1

	return top_squads

def get_top_rank1_squad_leaders(top_n):
	return get_top_rank1_leaders(top_n, 'leaders', META_UNITS_URL)

def get_top_rank1_fleet_commanders(top_n):
	return get_top_rank1_leaders(top_n, 'leaders', META_SHIPS_URL)

def get_top_rank1_arena_squads(top_n):
	return get_top_rank1_squads(top_n, 'squads', META_UNITS_URL)

def get_top_rank1_fleet_squads(top_n):
	return get_top_rank1_squads(top_n, 'squads', META_SHIPS_URL)

def get_top_rank1_reinforcements(top_n):
	return get_top_rank1_squads(top_n, 'reinforcements', META_SHIPS_URL)
