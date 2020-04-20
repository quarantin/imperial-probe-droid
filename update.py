#!/usr/bin/env python

import os
import sys
import json
import traceback
from config import load_config
from swgohhelp import api_swgoh_data
from recos import fetch_all_recos
from utils import http_get
from bs4 import BeautifulSoup

import DJANGO

from django.db import transaction

from swgoh.models import *

DEBUG = False

urls = {
	'cache/characters.json': 'https://swgoh.gg/api/characters/',
	'cache/ships.json':      'https://swgoh.gg/api/ships/',
	'cache/gear.json':       'https://swgoh.gg/api/gear/'
}

base_projects = [

	{
		'collection': 'skillList',
		'project': {
			'id': 1,
			'abilitiyReference': 1,
			'isZeta': 1,
		},
	},
	{
		'collection': 'unitsList',
		'match': {
			'rarity': 7,
			'obtainable': True,
		},
	},
]

lang_projects = [

	{
		'collection': 'abilityList',
		'project': {
			'id': 1,
			'nameKey': 1,
			'descKey': 1,
			'tierList': {
				'descKey': 1,
			},
		},
	},
	{
		'collection': 'equipmentList',
		'project': {
			'id': 1,
			'nameKey': 1,
		},
	},
	{
		'collection': 'unitsList',
		'project': {
			'baseId': 1,
			'nameKey': 1,
		},
		'match': {
			'rarity': 7,
			'obtainable': True,
		},
	},
]

async def fetch_all_collections(config):

	for filename, url in urls.items():
		response, error = await http_get(url)
		if not response:
			raise Exception('http_get failed!')

		fin = open(filename, 'w')
		fin.write(response.text)
		fin.close()

	if DEBUG is True:
		return

	# First download all base files
	for base_project in base_projects:

		project = dict(base_project)
		if 'project' in project:
			project.pop('project')

		print('Downloading base collection `%s`...' % project['collection'])
		data = await api_swgoh_data(config, project)

		filename = 'cache/%s.json' % project['collection']
		with open(filename, 'w') as fout:
			fout.write(json.dumps(data))

	# Then download language specific information
	for language, lang_code, lang_flag, lang_name in Player.LANGS:
		for lang_project in lang_projects:

			project = dict(lang_project)
			project['language'] = language,

			print('Downloading %s collection `%s`...' % (language, project['collection']))
			data = await api_swgoh_data(config, project)

			filename = 'cache/%s_%s.json' % (project['collection'], language)
			with open(filename, 'w') as fout:
				fout.write(json.dumps(data))

	print('All Done!')

def parse_translations_name(collection, key, context, language):

	filename = 'cache/%s_%s.json' % (collection, language)
	with open(filename, 'r') as fin:
		jsondata = json.loads(fin.read())
		with transaction.atomic():
			for entry in jsondata:

				obj, created = Translation.objects.update_or_create(string_id=entry[key], context=context, language=language)
				if obj.translation != entry['nameKey']:
					obj.translation = entry['nameKey']
					obj.save()

def parse_translations_desc(collection, key, context, language):

	filename = 'cache/%s_%s.json' % (collection, language)
	with open(filename, 'r') as fin:
		jsondata = json.loads(fin.read())
		with transaction.atomic():
			for entry in jsondata:

				tier_index = 1
				string_id = '%s/tier%02d' % (entry[key], tier_index)
				obj, created = Translation.objects.update_or_create(string_id=string_id, context=context, language=language)
				if obj.translation != entry['descKey']:
					obj.translation = entry['descKey']
					obj.save()

				tier_index = 2
				for tier in entry['tierList']:

					string_id = 'desc|%s|tier%02d' % (entry[key], tier_index)
					obj, created = Translation.objects.update_or_create(string_id=string_id, context=context, language=language)
					if obj.translation != tier['descKey']:
						obj.translation = tier['descKey']
						obj.save()

					tier_index += 1

WANTED_KEYS = {
	'UnitStat_Accuracy':                    'Potency',
	'UnitStat_Armor':                       'Armor',
	'UnitStat_CriticalDamage':              'Critical Damage',
	'UnitStat_Defense':                     'Defense',
	'UnitStat_DefensePenetration':          'Defense Penetration',
	'UnitStat_Health':                      'Health',
	'UnitStat_HealthSteal':                 'Health Steal',
	'UnitStat_MaxShield':                   'Protection',
	'UnitStat_Offense':                     'Offense',
	'UnitStat_DodgeNegateRating':           'Physical Accuracy',
	'UnitStat_AttackCriticalNegateRating':  'Physical Critical Avoidance',
	'UnitStat_AttackCriticalRating_TU5V':   'Physical Critical Chance',
	'UnitStat_DeflectionNegateRating':      'Special Accuracy',
	'UnitStat_AbilityCriticalNegateRating': 'Special Critical Avoidance',
	'UnitStat_Resistance':                  'Tenacity',
	'UnitStat_Speed':                       'Speed',
	'UnitStat_Suppression':                 'Resistance',
	'UnitStat_SuppressionPenetration':      'Resistance Penetration',
}

for i in range(1, 13):
	key = 'Unit_Tier%02d' % i
	WANTED_KEYS[key] = False

def parse_localization_files():

	context = 'localization'
	for language, lang_code, lang_flag, lang_name in Player.LANGS:

		filename = 'cache/Loc_%s.txt' % language.upper()
		if not os.path.exists(filename):
			print('Skipping missing translation file: %s' % filename)
			continue

		with open(filename, 'r') as fin:
			for line in fin:
				line = line.strip()
				if line.startswith('#'):
					continue

				string_id, translation = line.split('|')
				if string_id in WANTED_KEYS:
					if WANTED_KEYS[string_id] is not False:
						string_id = WANTED_KEYS[string_id]

					obj, created = Translation.objects.update_or_create(string_id=string_id, context=context, language=language, )
					if obj.translation != translation:
						obj.translation = translation
						obj.save()
						print('Updated %s translation for %s' % (lang_name, string_id))

def load_json(filename):

	with open(filename, 'r') as fin:
		return json.loads(fin.read())

def fix_url(url):
	return url.replace('http://swgoh.gg', '').replace('https://swgoh.gg', '').replace('//swgoh.gg', '')

def parse_gear():

	with transaction.atomic():
		gears = load_json('cache/gear.json')
		for gear in gears:

			stats       = gear.pop('stats')
			recipes     = gear.pop('recipes')
			ingredients = gear.pop('ingredients')

			gear['url']   = fix_url(gear['url'])
			gear['image'] = fix_url(gear['image'])

			try:
				equip = Gear.objects.get(base_id=gear['base_id'])

			except Gear.DoesNotExist:
				equip = Gear(base_id=gear['base_id'])

			for key, val in gear.items():
				if hasattr(equip, key):
					setattr(equip, key, val)

			equip.save()

def parse_units():

	with transaction.atomic():
		for filename in [ 'characters.json', 'ships.json' ]:
			units = load_json('cache/%s' % filename)
			for unit in units:

				char = dict(unit)

				gear_levels     = []
				categories      = char.pop('categories')
				ability_classes = char.pop('ability_classes')

				if 'pk' in char:
					char.pop('pk')

				if 'ship' in char:
					ship = char.pop('ship')

				if 'gear_levels' in char:
					gear_levels = char.pop('gear_levels')

				if 'url' in char:
					char['url'] = fix_url(char['url'])

				if 'image' in char:
					char['image'] = fix_url(char['image'])

				try:
					base_unit = BaseUnit.objects.get(base_id=unit['base_id'])
					BaseUnit.objects.filter(pk=base_unit.pk).update(**char)

				except BaseUnit.DoesNotExist:
					base_unit = BaseUnit(**char)
					base_unit.save()

				for category in categories:
					faction = BaseUnitFaction.is_supported_faction(category)
					if faction:
						obj, created = BaseUnitFaction.objects.update_or_create(unit=base_unit, faction=faction)

				for gear_level in gear_levels:

					slot = 1
					tier = gear_level['tier']

					for gear_id in gear_level['gear']:

						gear = Gear.objects.get(base_id=gear_id)

						try:
							created = False
							obj = BaseUnitGear.objects.get(unit=base_unit, tier=tier, slot=slot)

						except BaseUnitGear.DoesNotExist:
							created = True
							obj = BaseUnitGear(unit=base_unit, tier=tier, slot=slot)

						if created or obj.gear != gear:
							obj.gear = gear
							obj.save()

						slot += 1

UNITS_TO_IGNORE = [
	'AMILYNHOLDO_RADDUS',
	'AWAKENEDREY',
	'CAPITALFINALIZER_EVENT',
	'CAPITALRADDUS_EVENT',
	'FOTF_DEVASTATOR',
	'FOTF_VADER',
	'GENERALHUX_EVENT',
	'GRIEVOUS_MARQUEE',
	'KYLOREN_DUEL',
	'KYLORENUNMASKED_GLEVENT',
	'REY_DUEL',
	'REYJEDITRAINING_GLEVENT',
	'VULTUREDROID_tb',
]

def parse_skills():

	filename = 'cache/skillList.json'
	skill_list = load_json(filename)
	skills = {}
	for skill in skill_list:
		skill_id = skill['id']
		skills[skill_id] = skill

	filename = 'cache/unitsList.json'
	units = load_json(filename)
	with transaction.atomic():
		for unit in units:
			base_id = unit['baseId']

			if base_id.startswith('PVE_') or base_id in UNITS_TO_IGNORE:
				continue

			try:
				real_unit = BaseUnit.objects.get(base_id=base_id)
				unit_skills = unit['skillReferenceList']

				if 'crewList' in unit:
					for crew_member in unit['crewList']:
						unit_skills.extend(crew_member['skillReferenceList'])

				for skill in unit_skills:
					skill_id = skill['skillId']
					ability = skills[skill_id]
					ability_ref = ability['abilityReference']
					is_zeta = ability['isZeta']
					obj, created = BaseUnitSkill.objects.update_or_create(skill_id=skill_id, ability_ref=ability_ref, is_zeta=is_zeta, unit=real_unit)

			except BaseUnit.DoesNotExist:
				print("WARN: Missing unit from DB: %s" % base_id)
				continue

async def parse_zeta_report():

	url = 'https://swgoh.gg/stats/ability-report/?page=%d'
	try:
		response, error = await http_get(url % 1)
		soup = BeautifulSoup(response.content, 'html.parser')
		pagination_ul = soup.find('ul', { 'class': [ 'pagination', 'm-t-0' ] })
		pages = int(pagination_ul.find('a').text.replace('Page 1 of ', ''))

		page = 1
		while page < pages + 1:

			lis = soup.find_all('li', { 'class': 'character' })
			for li in lis:
				imgs = li.find_all('img')

				base_id = os.path.basename(os.path.dirname(imgs[0]['src']))
				skill_id = os.path.basename(os.path.dirname(imgs[1]['src']))

				div = li.find('div', { 'class': 'zeta-row' })
				zr = div.find_all('div')

				total_zetas      = int(zr[0].find('h3').text.replace(',', ''))
				of_all_zetas     = float(zr[1].find('h3').text.replace('%', ''))
				of_all_this_unit = float(zr[2].find('h3').text.replace('%', ''))
				of_g11_this_unit = float(zr[3].find('h3').text.replace('%', ''))

				try:
					unit = BaseUnit.objects.get(base_id=base_id)
				except BaseUnit.DoesNotExist:
					print("Could not find unit with base ID: %s" % base_id)
					continue

				try:
					zeta = ZetaStat.objects.get(unit=unit, skill_id=skill_id)
					zeta.total_zetas = total_zetas
					zeta.of_all_zetas = of_all_zetas
					zeta.of_all_this_unit = of_all_this_unit
					zeta.of_g11_this_unit = of_g11_this_unit

				except ZetaStat.DoesNotExist:
					zeta = ZetaStat(unit=unit, skill_id=skill_id, total_zetas=total_zetas, of_all_zetas=of_all_zetas, of_all_this_unit=of_all_this_unit, of_g11_this_unit=of_g11_this_unit)

				zeta.save()

			if page == pages:
				break

			page += 1
			response, error = await http_get(url % page)
			if not response or error:
				print("ERROR: %s" % error)
				return

			soup = BeautifulSoup(response.content, 'html.parser')

	except:
		print(traceback.format_exc())

async def parse_gear13_report():

	url = 'https://swgoh.gg/characters/data/g13/'
	try:
		response, error = await http_get(url)
		soup = BeautifulSoup(response.content, 'html.parser')
		rows = soup.find(id='characters').find('tbody').find_all('tr')
		for row in rows:

			cols = row.find_all('td')

			unit_name   = cols[0].text.strip()
			g13_count   = int(cols[1].text)
			total_count = int(cols[2].text)
			percentage  = float(cols[3].text.replace('%', ''))

			print("Processing %s..." % unit_name)
			try:
				unit = BaseUnit.objects.get(name=unit_name)

			except BaseUnit.DoesNotExist:
				print("Could not find unit with name '%s'. Skipping." % unit_name)
				continue

			try:
				g13_stat = Gear13Stat.objects.get(unit=unit)
				g13_stat.g13_count = g13_count
				g13_stat.total_count = total_count
				g13_stat.percentage = percentage

			except Gear13Stat.DoesNotExist:
				g13_stat = Gear13Stat(unit=unit, g13_count=g13_count, total_count=total_count, percentage=percentage)

			g13_stat.save()

	except:
		print(traceback.format_exc())

async def parse_relic_report():

	url = 'https://swgoh.gg/characters/data/relics/'
	try:
		response, error = await http_get(url)
		soup = BeautifulSoup(response.content, 'html.parser')
		rows = soup.find(id='characters').find('tbody').find_all('tr')
		for row in rows:

			cols = row.find_all('td')

			unit_name = cols[0].text.strip()
			unit = BaseUnit.objects.get(name=unit_name)
			try:
				s = RelicStat.objects.get(unit=unit)

			except RelicStat.DoesNotExist:
				s = RelicStat(unit=unit)

			s.relic1 = int(cols[1].text)
			s.relic2 = int(cols[2].text)
			s.relic3 = int(cols[3].text)
			s.relic4 = int(cols[4].text)
			s.relic5 = int(cols[5].text)
			s.relic6 = int(cols[6].text)
			s.relic7 = int(cols[7].text)
			s.g13_units = int(cols[22].text) or 1

			s.relic7_percentage = 100 * ((s.relic7) / s.g13_units)
			s.relic6_percentage = 100 * ((s.relic7 + s.relic6) / s.g13_units)
			s.relic5_percentage = 100 * ((s.relic7 + s.relic6 + s.relic5) / s.g13_units)
			s.relic4_percentage = 100 * ((s.relic7 + s.relic6 + s.relic5 + s.relic4) / s.g13_units)
			s.relic3_percentage = 100 * ((s.relic7 + s.relic6 + s.relic5 + s.relic4 + s.relic3) / s.g13_units)
			s.relic2_percentage = 100 * ((s.relic7 + s.relic6 + s.relic5 + s.relic4 + s.relic3 + s.relic2) / s.g13_units)
			s.relic1_percentage = 100 * ((s.relic7 + s.relic6 + s.relic5 + s.relic4 + s.relic3 + s.relic2 + s.relic1) / s.g13_units)

			s.save()

	except:
		print(traceback.format_exc())

def parse_rss_feeds(config):

	if 'feeds' not in config:
		print('No RSS feed defined in config.json')
		return

	for feed_name, feed_url in config['feeds'].items():

		try:
			feed = NewsFeed.objects.get(name=feed_name, url=feed_url)

		except NewsFeed.DoesNotExist:
			print("Saving RSS feed %s (%s)" % (feed_name, feed_url))
			feed = NewsFeed(name=feed_name, url=feed_url)
			feed.save()

async def save_all_recos():

	with transaction.atomic():
		recos = await fetch_all_recos()
		ModRecommendation.objects.all().delete()
		for reco in recos:

			base_id = reco.pop('base_id')
			reco['character'] = BaseUnit.objects.get(base_id=base_id)
			obj, created = ModRecommendation.objects.get_or_create(**reco)
			# TODO Why are mod recommendations created every time, but the total count does not increase?
			#print(reco)
			#if created is True:
			#	print('Added new mod recommendation for %s' % base_id)

async def __main__():

	forced_update = len(sys.argv) > 1 and sys.argv[1] == '--force'

	first_time = False
	version_url = 'https://api.swgoh.help/version'
	version_cache = 'cache/version.json'
	response, error = await http_get(version_url)
	new_version = json.loads(response.content)

	if not os.path.exists(version_cache):
		first_time = True
		old_version = new_version
	else:
		fin = open(version_cache)
		old_version = json.loads(fin.read())
		fin.close()

	if old_version == new_version and not first_time and not forced_update:
		print('Up-to-date: %s' % new_version)
		sys.exit()

	if forced_update:
		print('Forcing update: %s' % new_version)

	else:
		print('New version found, updating: %s' % new_version)

	fout = open(version_cache, 'w')
	fout.write(json.dumps(new_version))
	fout.close()

	config = load_config()

	await fetch_all_collections(config)

	parse_rss_feeds(config)
	parse_gear()
	parse_units()
	parse_skills()
	await parse_zeta_report()
	await parse_gear13_report()
	await parse_relic_report()
	parse_localization_files()

	await save_all_recos()

	for language, lang_code, lang_flag, lang_name in Player.LANGS:

		print('Parsing %s translations...' % language.lower())

		parse_translations_name('abilityList',   'id',     'abilities',  language)
		parse_translations_name('equipmentList', 'id',     'gear-names', language)
		parse_translations_name('unitsList',     'baseId', 'unit-names', language)
		parse_translations_desc('abilityList',   'id',     'skill-desc', language)

if __name__ == '__main__':
	import asyncio
	asyncio.get_event_loop().run_until_complete(__main__())
