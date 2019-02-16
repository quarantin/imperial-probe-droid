#!/usr/bin/python3

from utils import cache_expired, ensure_parents, get_units_dict

from swgohhelp import fetch_players

import os
import json
import socket
import requests
from bs4 import BeautifulSoup

db = {}

SWGOH_GG_API_URL = 'https://swgoh.gg/api'

META_UNITS_URL = 'https://swgoh.gg/meta-report/'
META_SHIPS_URL = 'https://swgoh.gg/fleet-meta-report/'
META_MODS_URL = 'https://swgoh.gg/mod-meta-report/rank_10/'
META_ZETAS_URL = 'https://swgoh.gg/ability-report/'

def download_unit_list(key, url):

	by_id = '%s-by-id' % key
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
		unit_list = requests.get(url).json()
		fout = open(cache, 'w+')
		fout.write(json.dumps(unit_list))
		fout.close()

	db[key] = unit_list
	db[by_id] = get_units_dict(unit_list, 'base_id')
	return db[by_id]

def get_char_list():
	return download_unit_list('chars', '%s/characters/' % SWGOH_GG_API_URL)

def get_ship_list():
	return download_unit_list('ships', '%s/ships/' % SWGOH_GG_API_URL)

def get_unit_list():
	units = get_char_list()
	units.update(get_ship_list())
	return units

def get_swgohgg_profile_url(ally_code):

	url = 'https://swgoh.gg/p/%s/' % ally_code

	try:
		response = requests.head(url)
		if response.status_code == 200:
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

def get_full_avatar_url(image, unit):

	image = os.path.basename(image)

	level = 'level' in unit and unit['level'] or 1
	gear = 'gearLevel' in unit and unit['gearLevel'] or 1
	rarity = 'starLevel' in unit and unit['starLevel'] or 0
	zetas = 'zetas' in unit and len(unit['zetas']) or 0

	#return 'https://api.swgoh.help/image/char/%s?level=%s&gear=%s&rarity=%s&zetas=%s' % (base_id, level, gear, rarity, zetas)
	url = 'http://%s/avatar/%s?level=%s&gear=%s&rarity=%s&zetas=%s' % (socket.gethostname(), image, level, gear, rarity, zetas)
	return url

def get_full_ship_avatar_url(ally_code, base_id):
	#return 'https://api.swgoh.help/image/ship/%s?rarity=%s&level=%s&bg=36393E&pilots=DEATHTROOPER-7-85-12-null%7CSHORETROOPER-7-85-12-null' % (base_id),
	pass
#
# Meta Reports
#

def get_top_rank1_leaders(top_n, html_id, url):

	top_leaders = []

	response = requests.get(url)
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

	response = requests.get(url)
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

def parse_modsets(td):

	modsets = sorted([ div['data-title'] for div in td.find_all('div') ])

	modsets += [''] * (3 - len(modsets))

	return modsets

def get_top_rank1_mods():

	top_mods = []

	response = requests.get(META_MODS_URL)
	soup = BeautifulSoup(response.text, 'lxml')
	trs = soup.select('li tr')

	for tr in trs:

		tds = tr.find_all('td')
		if not tds:
			continue

		char_name = tds[0].text.strip()
		modsets = parse_modsets(tds[1])
		prim_sq = tds[2].text.strip().split('/')
		prim_tr = tds[3].text.strip().split('/')
		prim_ci = tds[4].text.strip().split('/')
		prim_cr = tds[5].text.strip().split('/')

		for _sq in prim_sq:
			for _tr in prim_tr:
				for _ci in prim_ci:
					for _cr in prim_cr:
						top_mods.append([ char_name, 'swgoh.gg', 'Meta Report', modsets[0], modsets[1], modsets[2], 'Offense', _sq.strip(), 'Defense', _tr.strip(), _ci.strip(), _cr.strip()])
						#print("%s;swgoh.gg;Meta Report;Offense;%s;Defense;%s;%s;%s;%s" % (char_name, ';'.join(modsets), _sq.strip(), _tr.strip(), _ci.strip(), _cr.strip()))

	return top_mods
