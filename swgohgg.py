#!/usr/bin/env python

from utils import http_get

import os
import json
import socket
from bs4 import BeautifulSoup

import DJANGO
from swgoh.models import BaseUnit

db = {}

SWGOH_GG_API_URL = 'https://swgoh.gg/api'

META_UNITS_URL = 'https://swgoh.gg/meta-report/'
META_SHIPS_URL = 'https://swgoh.gg/fleet-meta-report/'
META_MODS_URL = 'https://swgoh.gg/mod-meta-report/rank_10/'
META_ZETAS_URL = 'https://swgoh.gg/ability-report/'

def get_swgohgg_profile_url(ally_code, no_check=False):

	url = 'https://swgoh.gg/p/%s/' % ally_code
	if no_check:
		return url

	try:
		response, error = http_get(url, headOnly=True)
		if not error and response.status_code == 200:
			return url
	except:
		pass

	return None

def get_swgohgg_player_unit_url(ally_code, base_id):

	from swgohhelp import get_simple_unit_name
	simple_name = get_simple_unit_name(base_id)
	url = 'https://swgoh.gg/p/%s/characters/%s' % (ally_code, simple_name)
	return url

def count_zetas(unit):
	zetas = 0
	if 'skills' in unit:
		for skill in unit['skills']:
			if 'isZeta' in skill and skill['isZeta'] is True and skill['tier'] == 8:
				zetas += 1
	return zetas

def get_full_avatar_url(config, image, unit):

	base_id = os.path.basename(os.path.dirname(image))
	alignment = BaseUnit.get_alignment(base_id)

	level, gear, rarity, zetas, relics = 1, 1, 0, 0, 0

	if unit is not None:
		level  = 'level'  in unit and unit['level']      or 1
		gear   = 'gear'   in unit and unit['gear']       or 1
		rarity = 'rarity' in unit and unit['rarity']     or 0
		zetas  = 'zetas'  in unit and len(unit['zetas']) or 0
		if zetas == 0:
			zetas = count_zetas(unit)
		relics = 'relic' in unit and unit['relic']['currentTier'] or 0
		relics = max(0, relics - 2)

	return 'http://%s/avatar/%s?level=%s&gear=%s&rarity=%s&zetas=%s&relics=%s&alignment=%s&version=1' % (config['server'], base_id, level, gear, rarity, zetas, relics, alignment)

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
