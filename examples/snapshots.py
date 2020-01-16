#!/usr/bin/env python

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import json
from datetime import datetime

from swgohhelp import *
from config import load_config

allycode = 349423868

def write_result(name, result):

	date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
	filename = '%s/%s-%s-%s.json' % (SNAPSHOTS_DIR, date, name, allycode)

	fout = open(filename, 'w')
	fout.write(json.dumps(result))
	fout.close()

results = {}

methods = {
	'guilds': api_swgoh_guilds,
	'players': api_swgoh_players,
	'roster': api_swgoh_roster,
	'units': api_swgoh_units,
}

project = {
	'allycodes': [
		allycode,
	],
}

SNAPSHOTS_DIR = './snapshots'
if not os.path.exists(SNAPSHOTS_DIR):
	os.mkdir(SNAPSHOTS_DIR)

config = load_config()

for name, api_method in methods.items():

	print('Calling api.swgoh.help/%s...' % name, file=sys.stderr)

	result = api_method(config, project)

	results[name] = result

	write_result(name, result)

name = 'crinolo'
api_method = api_crinolo

print('Calling Crinolo stats', file=sys.stderr)

result = api_method(config, results['units'])

results[name] = result

write_result(name, result)

print('Done.', file=sys.stderr)
