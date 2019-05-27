#!/usr/bin/python3

import os, json, requests

config = {}

def load_help():

	help_msgs = {}
	from commands import COMMANDS
	for cmd in COMMANDS:
		for alias in cmd['aliases']:
			help_msgs[alias] = cmd['help']

	return help_msgs

def write_config_to_file(config, config_file):

	data = json.dumps(config, indent=4, sort_keys=True)
	backup = '%s.bak' % config_file
	os.rename(config_file, backup)
	fin = open(config_file, 'w')
	fin.write(data)
	fin.close()

	os.remove(backup)

def parse_mod_primaries(filename='cache/mod-primaries.json'):

	fin = open(filename, 'r')
	data = fin.read()
	fin.close()
	data = json.loads(data)
	config['mod-primaries'] = { int(x): data[x] for x in data }

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

def parse_recommendations(recos_db={}):

	from recos import fetch_all_recos

	stats = {}
	recos_db['by-name'] = fetch_all_recos(config, index='name')
	recos_db['by-source'] = fetch_all_recos(config, index='source', index2='name')

	for unit, recos in recos_db['by-name'].items():
		extract_modstats(stats, recos)

	recos_db['stats'] = stats
	return recos_db

def parse_json(filename):
	filepath = os.path.join('cache', filename)
	fin = open(filepath, 'r')
	data = fin.read()
	fin.close()
	return json.loads(data)

def parse_skills(filename='skillList.en.json', lang='en'):

	skills = {}
	skill_list = parse_json(filename)

	for skill in skill_list:

		skill_id          = skill['id']
		skill_ability_ref = skill['abilityReference']

		skills[skill_id] = skill_ability_ref

	if 'skills' not in config:
		config['skills'] = {}

	config['skills'][lang] = skills

def parse_abilities(filename='abilityList.en.json', lang='en'):

	abilities = {}
	ability_list = parse_json(filename)

	for ability in ability_list:

		ability_id   = ability['id']
		ability_name = ability['nameKey']

		abilities[ability_id] = ability_name

	if 'abilities' not in config:
		config['abilities'] = {}

	config['abilities'][lang] = abilities

def save_config(config_file='config.json'):

	config_cpy = dict(config)

	to_remove = [
		'abilities',
		'allies',
		'help',
		'mod-primaries',
		'recos',
		'save',
		'separator',
		'skills',
		'stats',
	]

	for key in to_remove:
		if key in config_cpy:
			del config_cpy[key]

	if 'swgoh.help' in config_cpy:
		for key in [ 'access_token', 'access_token_expire' ]:
			if key in config_cpy['swgoh.help']:
				del config_cpy['swgoh.help'][key]

	write_config_to_file(config_cpy, config_file)

def load_config(bot=None, config_file='config.json'):

	if not config:
		fin = open(config_file, 'r')
		jsonstr = fin.read()
		fin.close()
		config.update(json.loads(jsonstr))
		parse_mod_primaries()

	if bot:
		config['help'] = load_help()
		config['recos'] = parse_recommendations()
		config['save'] = save_config
		config['separator'] = '`%s`' % ('-' * 27)

		parse_skills('skillList.en.json', 'en')
		parse_skills('skillList.fr.json', 'fr')
		parse_abilities('abilityList.en.json', 'en')
		parse_abilities('abilityList.fr.json', 'fr')

	return config
