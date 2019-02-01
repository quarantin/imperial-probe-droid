#!/usr/bin/python3

import os, json, requests

from commands import *
from utils import basicstrip

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

def parse_recommendations():

	url = config['sheets']['recommendations']['view']

	stats = {}

	recos_db = {}
	recos_db['by-name'] = {}
	recos_db['by-source'] = {}

	recos = download_spreadsheet(url, 12)
	next(recos)

	for reco in recos:

		name = basicstrip(reco[0])
		source = reco[1]

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

def save_config(config_file='config.json'):

	config_cpy = dict(config)

	to_remove = [
		'allies',
		'help',
		'recos',
		'save',
		'separator',
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

	if bot:
		print(json.dumps(config, indent=4, sort_keys=True))
		config['allies'] = parse_allies_db(bot.get_all_members())
		config['help'] = load_help()
		config['recos'] = parse_recommendations()
		config['save'] = save_config
		config['separator'] = '`%s`' % ('-' * 24)

	return config
