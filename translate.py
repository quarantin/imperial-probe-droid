#!/usr/bin/python3

import os
import sys
import json
import requests
from config import load_config
from swgohhelp import api_swgoh_data

import DJANGO

from django.db import transaction

from swgoh.models import Player, Translation

config = load_config()

collections = {
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
}


def fetch_all_collections(config):

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

def parse_json(collection, key, val, context, language):

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

#fetch_all_collections(config)

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
	sys.exit()

print('New version found, updating: %s' % new_version)
fout = open(version_cache, 'w')
fout.write(json.dumps(new_version))
fout.close()

for language, lang_code, lang_flag, lang_name in Player.LANGS:
	print('Parsing %s translations...' % language.lower())
	parse_json('unitsList', 'baseId', 'nameKey', 'unit-names', language)
	parse_json('equipmentList', 'id', 'nameKey', 'gear-names', language)
