#!/usr/bin/python3

import os
import pytz
import requests
import subprocess
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

SQUAD_ROLES = {
	1: 'Member',
	2: 'Leader',
	3: 'Commander',
	5: 'Reinforcement',
}

SHORTENER_URL = 'http://thelink.la/api-shorten.php?url='

PERCENT_STATS = [
	'%armor',
	'%resistance',
	'%physical-critical-chance',
	'%special-critical-chance',
	'%critical-damage',
	'%potency',
	'%tenacity',
]

FORMAT_LUT = {
	'%gear':   'gearLevel',
	'%gp':     'gp',
	'%level':  'level',
	'%rarity': 'starLevel',
	'%zetas':  'zetas',
}

STATS_LUT = {
    '%health':                      'Health',
    '%strength':                    'Strength',
    '%agility':                     'Agility',
    '%tactics':                     'Tactics',
    '%speed':                       'Speed',
    '%physical-damage':             'Physical Damage',
    '%special-damage':              'Special Damange',
    '%armor':                       'Armor',
    '%resistance':                  'Resistance',
    '%armor-penetration':           'Armor Penetration',
    '%resistance-penetration':      'Resistance Penetration',
    '%dodge-chance':                'Dodge Chance',
    '%deflection-chance':           'Delfection Chance',
    '%physical-critical-chance':    'Physical Critical Chance',
    '%special-critical-chance':     'Special Critical Chance',
    '%critical-damage':             'Critical Damage',
    '%potency':                     'Potency',
    '%tenacity':                    'Tenacity',
    '%health-steal':                'Health Steal',
    '%protection':                  'Protection',
    '%physical-accuracy':           'Physical Accuracy',
    '%special-accuracy':            'Special Accuracy',
    '%physical-critical-avoidance': 'Physical Critical Avoidance',
    '%special-critical-avoidance':  'Special Critical Avoidance',
}

def now(timezone):
	tz = pytz.timezone(timezone)
	return tz.localize(datetime.now())

def dotify(number):
	return '{:,}'.format(number)

def basicstrip(string):
	return string.replace(' ', '').replace('"', '').replace('(', '').replace(')', '').lower()

def emojistrip(string):
	return string.replace(' ', '').lower()

def add_stats(stats):

	if 'full' in stats:
		return stats

	if 'base' not in stats:
		res = stats

	else:
		res = stats['base']

		for substat in [ 'gear', 'mods' ]:

			for key in stats[substat]:
				val = stats[substat][key]
				if key not in res:
					res[key] = val
				else:
					res[key] += val

	stats['full'] = res
	return stats

def format_char_details(unit, fmt):

	if '%name' in fmt:
		from swgohgg import get_unit_list
		base_id = unit['defId']
		units = get_unit_list()
		fmt = fmt.replace('%name', units[base_id]['name'])

	if '%role' in fmt:

		role = unit['squadUnitType']
		fmt = fmt.replace('%role', SQUAD_ROLES[role])

	for pattern, json_key in FORMAT_LUT.items():
		if pattern in fmt:
			if json_key in unit:
				fmt = fmt.replace(pattern, str(unit[json_key]))
			else:
				fmt = fmt.replace(pattern, str(0))

	return fmt

def format_char_stats(stats, fmt):

	add_stats(stats)

	for pattern, key in STATS_LUT.items():

		if pattern in fmt:

			if key not in stats['full']:
				data = 0
			else:
				data = stats['full'][key]

			if pattern in [ '%critical-damage', '%potency', '%tenacity' ]:
				data = 100 * data

			data = round(data)

			if pattern in PERCENT_STATS:
				data = '%d%%' % data

			fmt = fmt.replace(pattern, str(data))

	return fmt

def update_source_code():
	script = 'scripts/update.sh'
	if os.path.exists(script):
		subprocess.call([ script ])

def exit_bot():

	# TODO send message on quit, like animated an
	# gif of an explosion or something like that.

	from bot import bot
	bot.loop.stop()
	bot.logout()
	bot.close()

	print('User initiated restart!')

def ensure_parents(filepath):
	os.makedirs(os.path.dirname(filepath), exist_ok=True)

def roundup(number):
	return Decimal(number).quantize(0, ROUND_HALF_UP)

def get_short_url(url):
	full_url = '%s%s' % (SHORTENER_URL, url)
	response = requests.get(full_url)
	return response.content.decode('utf-8')

def cache_expired(filepath):

	modified = datetime.fromtimestamp(os.path.getmtime(filepath))
	oldest = datetime.now() - timedelta(days=1)

	return modified < oldest

def lpad(number, limit=1000):

	pads = []

	copy = int(number.replace('%', '').strip())

	limits = []
	while limit > 1:
		limits.insert(0, limit)
		limit = limit / 10

	for limit in limits:
		if copy < limit:
			pads.append('\u202F\u202F')

	return '%s%s' % (''.join(pads), number)

def get_units_dict(units, base_id_key):

	d = {}

	for unit in units:
		base_id = unit[base_id_key]
		d[base_id] = unit

	return d

def get_mod_sets(config, mods):

	modsets = {}

	for mod in mods:

		modset = mod['set']
		if modset not in modsets:
			modsets[modset] = 0
		modsets[modset] += 1

	from constants import MODSETS_NEEDED
	for modset in MODSETS_NEEDED:
		needed = MODSETS_NEEDED[modset]
		if modset in modsets:
			modsets[modset] /= needed

	for modset in list(modsets):
		if modset == 0:
			del(modsets[modset])

	return modsets

def get_mod_sets_emojis(config, mods):
	from constants import MODSETS, EMOJIS

	emojis = []
	spacer = EMOJIS['']
	modsets = get_mod_sets(config, mods)
	for modset in MODSETS:
		if modset in modsets:
			set_name = MODSETS[modset]
			emoji = EMOJIS[ set_name.replace(' ', '').lower() ]
			emojis += [ emoji ] * int(modsets[modset])

	return sorted(emojis) + [ spacer ] * (3 - len(emojis))

def get_mod_primaries(config, mods):

	res = {}
	primaries = config['mod-primaries']

	for i in range(1, 7):
		res[i] = 'NA'

	for mod in mods:
		slot = mod['slot']
		prim_id = mod['primaryStat']['unitStat']
		primary = primaries[prim_id]
		res[slot] = primary

	return res

def get_stars_as_emojis(rarity):

	active = '★'
	inactive = '☆'

	stars = ''

	for i in range(1, 8):
		stars += i <= rarity and active or inactive

	return stars
