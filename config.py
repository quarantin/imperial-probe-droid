import os, sys, json, requests

DEFAULT_ROLE = 'IPD Admin'

class Config(dict):

	def get_server_url(self):
		schema = 'http'
		if 'schema' in self:
			schema = self['schema']

		if 'server' in self:
			return '%s://%s' % (schema, self['server'])

		raise Exception('Can\'t find \'server\' in JSON configuration.')

config = Config()

def get_root_dir():
	this_file = os.path.realpath(__file__)
	this_folder = os.path.dirname(this_file)
	return this_folder

def load_help():

	help_msgs = {}
	from commands import COMMANDS
	for cmd in COMMANDS:
		for alias in cmd['aliases']:
			help_msgs[alias] = cmd['help']

	config['help'] = help_msgs

def write_config_to_file(config, config_file):

	data = json.dumps(config, indent=4)
	backup = '%s.bak' % config_file
	os.rename(config_file, backup)
	fin = open(config_file, 'w')
	fin.write(data)
	fin.close()

	os.remove(backup)

def parse_mod_primaries(filename='cache/mod-primaries.json'):

	root = get_root_dir()
	filename = '%s/%s' % (root, filename)
	fin = open(filename, 'r')
	data = fin.read()
	fin.close()
	data = json.loads(data)
	config['mod-primaries'] = { int(x): data[x] for x in data }

def parse_json(filename):
	filepath = os.path.join('cache', filename)
	if not os.path.exists(filepath):
		return []

	fin = open(filepath, 'r')
	data = fin.read()
	fin.close()
	return json.loads(data)

def save_config(config_file='config.json'):

	config_cpy = dict(config)

	to_remove = [
		'abilities',
		'allies',
		'bot',
		'help',
		'mod-primaries',
		'redis',
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

def load_config(config_file='config.json'):

	if not config:

		config_path = '%s/%s' % (get_root_dir(), config_file)
		fin = open(config_path, 'r')
		jsonstr = fin.read()
		fin.close()
		config.update(json.loads(jsonstr))
		parse_mod_primaries()

		config['save'] = save_config
		config['separator'] = '`%s`' % ('-' * 27)
		config['debug'] = 'debug' in config and config['debug']
		config['role'] = DEFAULT_ROLE

		import redis
		config.redis = redis.Redis()

	return config

def setup_logs(facility, filename, level=None):

	import logging
	logger = logging.getLogger(facility)
	level = (facility == 'discord') and logging.WARNING or (level is not None and level or logging.DEBUG)
	logger.setLevel(level)
	handler = logging.FileHandler(filename=filename, encoding='utf-8', mode='a')
	handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
	logger.addHandler(handler)
	return logger
