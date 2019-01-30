#!/usr/bin/python3

import os, json, requests

from utils import basicstrip

def load_help():
	from ipd import CMDS

	help_msgs = {}
	for cmd in CMDS:
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

def parse_allies_db(config):

	url = config['sheets']['allies']['view']

	allies_db = {}
	allies_db['by-ally-code'] = {}
	allies_db['by-game-nick'] = {}
	allies_db['by-discord-nick'] = {}

	allies = download_spreadsheet(url, 3)
	next(allies)

	for ally in allies:

		game_nick, discord_nick, ally_code = ally

		allies_db['by-ally-code'][ally_code] = ally
		allies_db['by-game-nick'][game_nick] = ally
		allies_db['by-discord-nick'][discord_nick] = ally

	return allies_db

def parse_recommendations(config):

	url = config['sheets']['recommendations']['view']

	recos_db = {}
	recos_db['by-source'] = {}

	recos = download_spreadsheet(url, 12)
	next(recos)

	for reco in recos:

		name = basicstrip(reco[0])
		source = reco[1]

		if source not in recos_db['by-source']:
			recos_db['by-source'][source] = {}

		if name not in recos_db:
			recos_db[name] = []

		if name not in recos_db['by-source'][source]:
			recos_db['by-source'][source][name] = []

		recos_db[name].append(reco)
		recos_db['by-source'][source][name].append(reco)

	return recos_db

def save_config(config, config_file='config.json'):

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

def load_config(config_file='config.json'):

	fin = open(config_file, 'r')
	jsonstr = fin.read()
	fin.close()

	config = json.loads(jsonstr)
	print(json.dumps(config, indent=4, sort_keys=True))

	config['allies'] = parse_allies_db(config)
	config['help'] = load_help()
	config['recos'] = parse_recommendations(config)
	config['save'] = save_config
	config['separator'] = '`%s`' % ('-' * 30)

	return config
