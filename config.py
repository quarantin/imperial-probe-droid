#!/usr/bin/python3

import os, json, requests

from utils import basicstrip

UNITS_SHORT_NAMES = {
	'aa':    'Admiral Ackbar',
	'bf':    'Boba Fett',
	'cb':    'Chewbacca',
	'cc':    'Chief Chirpa',
	'chs':   'Captain Han Solo',
	'cls':   'Commander Luke Skywalker',
	'cup':   'Coruscant Underworld Police',
	'cwc':   'Clone Wars Chewbacca',
	'dk':    'Director Krennic',
	'dn':    'Darth Nihilus',
	'dv':    'Darth Vader',
	'ee':    'Ewok Elder',
	'ep':    'Emperor Palpatine',
	'foe':   'First Order Executioner',
	'fox':   'First Order Executioner',
	'foo':   'First Order Officer',
	'fostp': 'First Order SF TIE Pilot',
	'fost':  'First Order Stormtrooper',
	'fotp':  'First Order TIE Pilot',
	'gk':    'General Kenobi',
	'gat':   'Grand Admiral Thrawn',
	'gmt':   'Grand Moff Tarkin',
	'gmy':   'Grand Master Yoda',
	'hy':    'Hermit Yoda',
	'hoda':  'Hermit Yoda',
	'hyoda': 'Hermit Yoda',
	'hs':    'Han Solo',
	'hst':   'Stormtrooper Han',
	'ipd':   'Imperial Probe Droid',
	'jf':    'Jango Fett',
	'jka':   'Jedi Knight Anakin',
	'jkg':   'Jedi Knight Guardian',
	'jkr':   'Jedi Knight Revan',
	'jtr':   'Rey (Jedi Training)',
	'kr':    'Kylo Ren',
	'kru':   'Kylo Ren (Unmasked)',
	'mt':    'Mother Talzin',
	'qgj':   'Qui-Gon Jinn',
	'sth':   'Stormtrooper Han',
	'rex':   'CT-7567',
	'rolo':  'Rebel Officer Leia Organa',
	'rp':    'Resistance Pilot',
	'rjt':   'Rey (Jedi Training)',
	'vsc':   'Veteran Smuggler Chewbacca',
	'vshs':  'Veteran Smuggler Han Solo',
	'yhs':   'Young Han Solo',
	'ylc':   'Young Lando Calrissian',
}

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
	config['units-short-names'] = UNITS_SHORT_NAMES
	print(json.dumps(config, indent=4, sort_keys=True))

	config['allies'] = parse_allies_db(config)
	config['help'] = load_help()
	config['recos'] = parse_recommendations(config)
	config['save'] = save_config
	config['separator'] = '`%s`' % ('-' * 30)

	return config
