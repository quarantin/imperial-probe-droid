#!/usr/bin/python3

import os, json, requests

from commands import *
from utils import basicstrip, get_short_url

config = {}

def load_help():

	help_msgs = {}
	for cmd in COMMANDS:
		for alias in cmd['aliases']:
			help_msgs[alias] = cmd['help']

	return help_msgs

def write_config_to_file(config, config_file):

	backup = '%s.bak' % config_file
	os.rename(config_file, backup)

	fin = open(config_file, 'w')
	fin.write(json.dumps(config, indent=4, sort_keys=True))
	fin.close()

	os.remove(backup)

def download_spreadsheet(url, cols):

	content = []
	response = requests.get(url)
	response.encoding = 'utf-8'

	lines = response.text.split('\r\n')
	for line in lines:
		toks = line.split(',')
		content.append(toks[0:cols])

	return iter(content)

def parse_allies_db(members):

	url = config['sheets']['allies']['view']

	allies_db = {}
	allies_db['by-mention'] = {}
	allies_db['by-ally-code'] = {}
	allies_db['by-game-nick'] = {}
	allies_db['by-discord-nick'] = {}

	allies = download_spreadsheet(url, 3)
	next(allies)

	for ally in allies:

		game_nick, discord_nick, ally_code = ally

		allies_db['by-ally-code'][ally_code] = ally
		allies_db['by-game-nick'][game_nick] = ally

		if discord_nick:
			allies_db['by-discord-nick'][discord_nick] = ally

	for member in members:

		raw_nick = member.display_name or member.nick or member.name
		nick = '@%s' % raw_nick
		if nick not in allies_db['by-discord-nick']:
			continue

		mention1 = '<@%s>' % member.id
		mention2 = '<@!%s>' % member.id
		ally_code = allies_db['by-discord-nick'][nick]

		if raw_nick not in allies_db['by-mention']:
			allies_db['by-mention'][raw_nick] = ally_code

		if mention1 not in allies_db['by-mention']:
			allies_db['by-mention'][mention1] = ally_code

		if mention2 not in allies_db['by-mention']:
			allies_db['by-mention'][mention2] = ally_code

	return allies_db

def parse_mod_primaries(filename='cache/mod-primaries.json'):

	fin = open(filename, 'r')
	data = fin.read()
	fin.close()
	data = json.loads(data)
	config['mod-primaries'] = { int(x): data[x] for x in data }

def count_recos_per_source(source, recos):

	count = 0
	for reco in recos:
		if reco[1] == source:
			count += 1

	return count

def extract_modstats(stats, recos):

	for reco in recos:

		source = reco[1]
		count = count_recos_per_source(source, recos)

		for i in range(6, 12):

			slot = i - 5
			primary = reco[i]

			if slot not in stats:
				stats[slot] = {}

			if primary not in stats[slot]:
				stats[slot][primary] = {}

			if source not in stats[slot][primary]:
				stats[slot][primary][source] = 0.0
			stats[slot][primary][source] += 1.0 / count

def parse_recommendations(recos=None, recos_db={}):

	from swgohgg import get_top_rank1_mods
	get_top_rank1_mods()
	url = config['sheets']['recommendations']['view']

	stats = {}

	if 'by-name' not in recos_db:
		recos_db['by-name'] = {}

	if 'by-source' not in recos_db:
		recos_db['by-source'] = {}

	if not recos:
		recos = download_spreadsheet(url, 16)
		next(recos)

	for reco in recos:

		name = basicstrip(reco[0])
		source = reco[1]
		if not name or not source:
			continue

		if name not in recos_db['by-name']:
			recos_db['by-name'][name] = []

		if source not in recos_db['by-source']:
			recos_db['by-source'][source] = {}

		if name not in recos_db['by-source'][source]:
			recos_db['by-source'][source][name] = []

		recos_db['by-name'][name].append(reco)
		recos_db['by-source'][source][name].append(reco)

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
	]

	for key in to_remove:
		if key in config_cpy:
			del config_cpy[key]

	write_config_to_file(config_cpy, config_file)

def load_config(bot=None, config_file='config.json'):

	if not config:
		fin = open(config_file, 'r')
		jsonstr = fin.read()
		fin.close()
		config.update(json.loads(jsonstr))
		parse_mod_primaries()
		if 'short-urls' not in config:
			config['short-urls'] = {}

		if 'source' in config:
			source_url = config['source']
			if source_url not in config['short-urls']:
				config['short-urls'][source_url] = get_short_url(source_url)

		if 'sheets' in config:

			for sheet in [ 'allies', 'recommendations' ]:
				if sheet not in config['sheets']:
					continue

				if 'edit' in config['sheets'][sheet]:
					edit_url = config['sheets'][sheet]['edit']
					if edit_url not in config['short-urls']:
						config['short-urls'][edit_url] = get_short_url(edit_url)

				if 'view' in config['sheets'][sheet]:
					view_url = config['sheets'][sheet]['view']
					if view_url not in config['short-urls']:
						config['short-urls'][view_url] = get_short_url(view_url)

	if bot:
		print(json.dumps(config, indent=4, sort_keys=True))
		from swgohgg import get_top_rank1_mods
		recos_db = parse_recommendations()
		swgohgg_recos = get_top_rank1_mods()
		parse_recommendations(swgohgg_recos, recos_db)
		config['allies'] = parse_allies_db(bot.get_all_members())
		config['help'] = load_help()
		config['recos'] = recos_db
		config['save'] = save_config
		config['separator'] = '`%s`' % ('-' * 27)

		parse_skills('skillList.en.json', 'en')
		parse_skills('skillList.fr.json', 'fr')
		parse_abilities('abilityList.en.json', 'en')
		parse_abilities('abilityList.fr.json', 'fr')

	return config
