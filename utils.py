# -*- coding: utf-8 -*-

import os
import json
import pytz
import aiohttp
import requests
import subprocess
import traceback
from fuzzywuzzy import fuzz
from requests.exceptions import HTTPError
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

import DJANGO
from swgoh.models import BaseUnit, BaseUnitSkill, Translation

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
	'%gear':   'gear',
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
	'%special-damage':              'Special Damage',
	'%armor':                       'Armor',
	'%resistance':                  'Resistance',
	'%armor-penetration':           'Armor Penetration',
	'%resistance-penetration':      'Resistance Penetration',
	'%dodge-chance':                'Dodge Chance',
	'%deflection-chance':           'Deflection Chance',
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

def rpad(data, length, char=' '):
	string = str(data)
	padlen = max(0, length - len(string))
	return string + char * padlen

def lpad(data, length, char=' '):
	string = str(data)
	padlen = max(0, length - len(string))
	return char * padlen + string

def is_numeric(string):
	try:
		float(string)
		return True
	except ValueError:
		return False

def load_json(filename):
	with open(filename, 'r') as fin:
		return json.loads(fin.read())

def dump_json(filename, data, indent=None):
	with open(filename, 'w') as fout:
		fout.write(json.dumps(data, indent=indent))

def fix_swgohgg_url(url):
	return url.replace('http://swgoh.gg', '').replace('https://swgoh.gg', '').replace('//swgoh.gg', '')

def local_time(date=None, timezone='Europe/Paris'):
	if date is None:
		date = datetime.now()
	return pytz.timezone(timezone).localize(date)

def dotify(number):
	return '{:,}'.format(roundup(number))

async def http_get(url, headOnly=False):

	try:
		if headOnly is True:
			response = requests.head(url)
		else:
			response = requests.get(url)

		response.raise_for_status()

	except HTTPError as http_err:
		return (None, 'HTTP error occured: %s' % http_err)

	except Exception as err:
		return (None, 'Other error occured: %s' % err)

	else:
		return response, False

async def http_post(url, *args, **kwargs):
	errmsg = 'Unknown Error'
	async with aiohttp.ClientSession() as session:
		async with session.post(url, *args, **kwargs) as response:
			try:
				return await response.json(), False
			except Exception as err:
				errmsg = str(err)
				print(err)
				print(traceback.format_exc())

	return None, errmsg

removable_chars = """`'"()[]{}"""

replaceable_chars = {
	'é': 'e',
	'É': 'E',
	'î': 'i',
	'Î': 'I',
}

def basicstrip(string):

	for char in string:

		if char in removable_chars:
			string = string.replace(char, '')

		elif char in replaceable_chars:
			string = string.replace(char, replaceable_chars[char])

	return string.lower()

ignore_translate_errors = {
	'NA': True,
}

def translate(string_id, language='eng_us'):

	langs = [ language ]
	if language != 'eng_us':
		langs.append('eng_us')

	for lang in langs:

		try:
			t = Translation.objects.get(string_id=string_id, language=lang)
			return t.translation

		except Translation.DoesNotExist:
			pass

	if string_id not in ignore_translate_errors:
		print('WARN: Missing translation for string ID: %s (%s)' % (string_id, language))

	return string_id

def translate_multi(string_ids, language='eng_us'):

	translations = []
	for string_id in string_ids:
		translations.append(translate(string_id, language))

	return translations

def get_ability_name(skill_id, language):

	try:
		skill = BaseUnitSkill.objects.get(skill_id=skill_id)
		try:
			t = Translation.objects.get(string_id=skill.ability_ref, language=language)
			return t.translation

		except Translation.DoesNotExist:
			print("Missing translation for string ID %s" % skill.ability_ref)

	except BaseUnitSkill.DoesNotExist:
		pass

	except BaseUnitSkill.MultipleObjectsReturned:
		skills = list(BaseUnitSkill.objects.filter(skill_id=skill_id).values())
		if len(skills) > 1:
			print('* Warning: Duplicate skill for skill ID: %s' % skill_id)
			i = 1
			for skill in skills:
				print('# %d:' % i)
				print(json.dumps(skill, indent=4))
				i += 1
	# TODO
	#print('No ability name found for skill id: %s' % skill_id, file=sys.stderr)
	return None

def format_char_details(unit, fmt):

	if '%name' in fmt:
		base_id = unit['defId']
		units = BaseUnit.objects.all().values('name', 'base_id')
		chars = { x['base_id']: { 'name': x['name'] } for x in units }
		fmt = fmt.replace('%name', chars[base_id]['name'])

	if '%role' in fmt:
		fmt = fmt.replace('%role', unit['role'].title())

	for pattern, json_key in FORMAT_LUT.items():
		if pattern in fmt:
			if json_key in unit:
				fmt = fmt.replace(pattern, str(unit[json_key]))
			else:
				fmt = fmt.replace(pattern, str(0))

	return fmt

def format_char_stats(stats, fmt):

	for pattern, key in STATS_LUT.items():

		if pattern in fmt:

			if key not in stats['stats']['final']:
				print('MISSING STAT KEY: %s\n%s' % (key, stats['stats']['final']))
				data = 0
			else:
				data = stats['stats']['final'][key]

			if pattern in PERCENT_STATS:
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

def roundup(number):
	return Decimal(number).quantize(0, ROUND_HALF_UP)

def expired(expiration_date):
	return expiration_date < datetime.now()

def get_dict_by_index(dict_list, index_key):

	d = {}

	for a_dict in dict_list:
		index = a_dict[index_key]
		if index not in d:
			d[index] = []

		d[index].append(a_dict)

	return d

def get_banner_emoji(banner_logo):
	from constants import EMOJIS

	if not banner_logo:
		return EMOJIS['noguild']

	banner = banner_logo.replace('guild_icon_', '').replace('.png', '').lower()

	# FIXME: Find a better way...
	# Replace triangle banner name to avoid collision with triangle mod shape
	banner = banner.replace('triangle', 'triangle-2')

	emoji = banner in EMOJIS and EMOJIS[banner] or EMOJIS['noguild']
	return emoji

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

def get_star():
	return '★'

def get_stars_as_emojis(rarity):

	active = '★'
	inactive = '☆'

	stars = ''

	for i in range(1, 8):
		stars += i <= rarity and active or inactive

	return stars

def get_field_legend(config, inline=True, meta=None):

	from constants import EMOJIS

	emoji_cg = EMOJIS['capitalgames']
	emoji_cr = EMOJIS['crouchingrancor']
	emoji_gg = EMOJIS['swgoh.gg']

	swgohgg = 'swgoh.gg ' + (meta or '')

	return {
		'name': '== Legend ==',
		'value': '\u202F%s EA / Capital Games\n\u202F%s Crouching Rancor\n\u202F%s %s\n' % (emoji_cg, emoji_cr, emoji_gg, swgohgg),
		'inline': inline,
	}

MODSETS_TO_FIX = {
	'Crit Chance': 'Critical Chance',
	'Crit Damage': 'Critical Damage',
	'Crit Avoidance': 'Critical Avoidance',
}

def parse_modsets(td):

	modsets = []
	for div in td.find_all('div'):
		modset = div['data-title']
		if modset in MODSETS_TO_FIX:
			modset = MODSETS_TO_FIX[modset]
		modsets.append(modset)

	modsets += [''] * (3 - len(modsets))

	return modsets

def get_available_timezones():

	from pytz import common_timezones

	timezones = list(common_timezones)

	# We don't want users to select GMT or UTC because these
	# timezones don't take daylight saving times into account.
	timezones.remove('GMT')
	timezones.remove('UTC')

	return timezones

def is_supported_timezone(tzinfo, timezones):

	for tz in timezones:

		tzl = tz.lower()
		if tzl == tzinfo:
			return tz

		tokens = tzl.split('/')
		if len(tokens) == 2 and tzinfo == tokens[1]:
			return tz

	return False

def get_fuzz_ratio(str1, str2):
	return fuzz.ratio(str1, str2)

def count_recos_per_source(source, recos):

	count = 0
	for reco in recos:
		if reco['source'] == source:
			count += 1

	return count

def extract_modstats(stats, recos):

	for reco in recos:

		source = reco['source']
		count = count_recos_per_source(source, recos)

		for slot in [ 'square', 'arrow', 'diamond', 'triangle', 'circle', 'cross' ]:

			primary = reco[slot]

			if slot not in stats:
				stats[slot] = {}

			if primary not in stats[slot]:
				stats[slot][primary] = {}

			if source not in stats[slot][primary]:
				stats[slot][primary][source] = 0.0
			stats[slot][primary][source] += 1.0 / count

def extract_modstats_from_roster(stats, roster):

	from constants import MODSLOTS, UNIT_STATS

	for unit in roster:

		if 'mods' not in unit or not unit['mods']:
			continue

		for mod in unit['mods']:

			slot = MODSLOTS[ mod['slot'] ].lower()
			if slot not in stats:
				stats[slot] = {}

			primary = UNIT_STATS[ mod['primaryStat']['unitStat'] ].replace('%', '').strip()
			if primary not in stats[slot]:
				stats[slot][primary] = 0

			stats[slot][primary] += 1
