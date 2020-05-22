#!/usr/bin/env python

import os
import sys
import json
from config import load_config
from swgohhelp import SwgohHelp
from utils import http_get

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

async def fetch_all_collections(swgohhelp):

	print('Downloading game data.')
	print('This might take a while.')

	for filename, url in urls.items():
		response, error = await http_get(url)
		if not response:
			raise Exception('http_get failed!')

		fin = open(filename, 'w')
		fin.write(response.text)
		fin.close()

	# First download all base files
	for base_project in base_projects:

		project = dict(base_project)
		if 'project' in project:
			project.pop('project')

		print('Downloading base collection `%s`...' % project['collection'])
		data = await swgohhelp.api_swgoh_data(project)

		filename = 'cache/%s.json' % project['collection']
		with open(filename, 'w') as fout:
			fout.write(json.dumps(data))

	# Then download language specific information
	for language, lang_code, lang_flag, lang_name in Player.LANGS:
		for lang_project in lang_projects:

			project = dict(lang_project)
			project['language'] = language

			print('Downloading %s collection `%s`...' % (language, project['collection']))
			data = await swgohhelp.api_swgoh_data(project)

			filename = 'cache/%s_%s.json' % (project['collection'], language)
			with open(filename, 'w') as fout:
				fout.write(json.dumps(data))

	print('OK')

async def __main__():

	forced_update = '-f' in sys.argv or '--force' in sys.argv

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
		print('Forcing update!')
		print('Old version: %s' % old_version)
		print('New version: %s' % new_version)

	else:
		print('New version found, updating!')
		print('Old version: %s' % old_version)
		print('New version: %s' % new_version)

	fout = open(version_cache, 'w')
	fout.write(json.dumps(new_version))
	fout.close()

	config = load_config()
	swgohhelp = SwgohHelp(config)

	await fetch_all_collections(swgohhelp)

if __name__ == '__main__':
	import asyncio
	asyncio.get_event_loop().run_until_complete(__main__())
