import os, sys, json, requests

config = {}

def load_help():

	help_msgs = {}
	from commands import COMMANDS
	for cmd in COMMANDS:
		for alias in cmd['aliases']:
			help_msgs[alias] = cmd['help']

	config['help'] = help_msgs

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

def parse_json(filename):
	filepath = os.path.join('cache', filename)
	fin = open(filepath, 'r')
	data = fin.read()
	fin.close()
	return json.loads(data)

def parse_skills(filename='skillList.json'):

	skills = {}
	skill_list = parse_json(filename)

	for skill in skill_list:

		skill_id          = skill['id']
		skill_is_zeta     = skill['isZeta']
		skill_ability_ref = skill['abilityReference']

		skills[skill_id] = {
			'isZeta': skill_is_zeta,
			'abilityReference': skill_ability_ref,
		}

	config['skills'] = skills

def save_config(config_file='config.json'):

	config_cpy = dict(config)

	to_remove = [
		'abilities',
		'allies',
		'bot',
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

def dprint(message):
	if config and 'debug' in config and config['debug'] is True:
		print('DEBUG: %s' % message, file=sys.stderr)

def load_config(bot=None, config_file='config.json'):

	if not config:
		fin = open(config_file, 'r')
		jsonstr = fin.read()
		fin.close()
		config.update(json.loads(jsonstr))
		parse_mod_primaries()

		config['save'] = save_config
		config['separator'] = '`%s`' % ('-' * 27)
		config['debug'] = 'debug' in config and config['debug']

		parse_skills()

	return config
