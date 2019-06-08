#!/usr/bin/env python

import os
import sys
import json
import requests
from config import load_config
from swgohhelp import api_swgoh_data

import DJANGO

from django.db import transaction

from swgoh.models import Player, Translation, BaseUnit, BaseUnitFaction, BaseUnitSkill

DEBUG = True

collections = {

	'abilityList': {
		'project': {
			'id': 1,
			'nameKey': 1,
		},
	},
	'equipmentList': {
		'project': {
			'id': 1,
			'nameKey': 1,
		},
	},
	'unitsList': {
		'match': {
			'rarity': 7,
			'obtainable': True,
		},
		'project': {
			'baseId': 1,
			'nameKey': 1,
		},
	},
	'skillList': {
		'project': {
			'id': 1,
			'abilitiyReference': 1,
			'isZeta': 1,
		},
	},
}

urls = {
	'cache/characters.json': 'https://swgoh.gg/api/characters/',
	'cache/ships.json':      'https://swgoh.gg/api/ships/',
}

def fetch_all_collections(config):

	for filename, url in urls.items():
		response = requests.get(url)
		if response.status_code != 200:
			raise Exception('requests.get failed!')

		fin = open(filename, 'w')
		fin.write(response.text)
		fin.close()

	if DEBUG is True:
		return

	# First download all base files
	for collection, data in collections.items():

		print('Downloading base collection `%s`...' % collection)

		data = api_swgoh_data(config, {
			'collection': collection,
		})

		filename = 'cache/%s_base.json' % collection
		with open(filename, 'w') as fout:
			fout.write(json.dumps(data))

	# Then download language specific information
	for language, lang_code, lang_flag, lang_name in Player.LANGS:
		for collection, params in collections.items():

			print('Downloading %s collection `%s`...' % (language, collection))

			project = {
				'collection': collection,
				'language': language,
			}

			if 'match' in params:
				project['match'] = params['match']

			if 'project' in params:
				project['project'] = params['project'],

			data = api_swgoh_data(config, project)

			filename = 'cache/%s_%s.json' % (collection, language)
			with open(filename, 'w') as fout:
				fout.write(json.dumps(data))

	print('All Done!')

def parse_translations(collection, key, val, context, language):

	filename = 'cache/%s_%s.json' % (collection, language)
	with open(filename, 'r') as fin:
		jsondata = json.loads(fin.read())
		with transaction.atomic():
			for entry in jsondata:

				obj, created = Translation.objects.update_or_create(string_id=entry[key], context=context, language=language)
				if obj.translation != entry[val]:
					obj.translation = entry[val]
					obj.save()

#	print('Saving Results to database')
#	with transaction.atomic():
#		for item in result:
#			Translation(string_id=item['id'], translation=item['nameKey'], language=language).save()

#for language, lang_code, lang_flag, lang_name in Player.LANGS:

#	language = 'fre_fr'
#	lang_name = 'French'

	#print('Deleting all previous translations for %s' % lang_name)
	#Translation.objects.filter(language=language).delete()

	#fetch_unit_names(config, language)

	#fetch_gear_names(config, language)

#	break

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

		filename = 'Loc_%s.txt' % language.upper()
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

def parse_units():

	with transaction.atomic():
		for filename in [ 'cache/characters.json', 'cache/ships.json' ]:
			units = load_json(filename)
			for unit in units:

				char = dict(unit)

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

				base_unit, created = BaseUnit.objects.update_or_create(base_id=unit['base_id'])

				BaseUnit.objects.filter(pk=base_unit.pk).update(**char)

				for category in categories:
					faction = BaseUnitFaction.is_supported_faction(category)
					if faction:
						obj, created = BaseUnitFaction.objects.update_or_create(unit=base_unit, faction=faction)

def parse_skills():

	filename = 'cache/skillList_base.json'
	skill_list = load_json(filename)
	skills = {}
	for skill in skill_list:
		skill_id = skill['id']
		skills[skill_id] = skill['isZeta']

	filename = 'cache/unitsList_base.json'
	units = load_json(filename)
	with transaction.atomic():
		for unit in units:
			base_id = unit['baseId']
			try:
				real_unit = BaseUnit.objects.get(base_id=base_id)
			except BaseUnit.DoesNotExist:
				continue
			unit_skills = unit['skillReferenceList']
			for skill in unit_skills:
				skill_id = skill['skillId']
				is_zeta = skills[skill_id]
				obj, created = BaseUnitSkill.objects.update_or_create(skill_id=skill_id, is_zeta=is_zeta, unit=real_unit)

first_time = False
version_url = 'https://api.swgoh.help/version'
version_cache = 'cache/version.json'
response = requests.get(version_url)
new_version = response.json()

if not os.path.exists(version_cache):
	first_time = True
	old_version = new_version
else:
	fin = open(version_cache)
	old_version = json.loads(fin.read())
	fin.close()

if old_version == new_version and not first_time:
	print('Up-to-date: %s' % new_version)
	# TODO Uncomment this line
	#sys.exit()

print('New version found, updating: %s' % new_version)
fout = open(version_cache, 'w')
fout.write(json.dumps(new_version))
fout.close()

config = load_config()

fetch_all_collections(config)

parse_units()
parse_skills()
parse_localization_files()

for language, lang_code, lang_flag, lang_name in Player.LANGS:
	print('Parsing %s translations...' % language.lower())
	parse_translations('abilityList',   'id', 'nameKey', 'abilities',  language)
	parse_translations('equipmentList', 'id', 'nameKey', 'gear-names', language)
	parse_translations('unitsList', 'baseId', 'nameKey', 'unit-names', language)
