#!/usr/bin/python3

from utils import basicstrip
from swgoh import get_all_units

DEFAULT_FORMAT = '**%name**%leader%reinforcement\n  P:%power H:%health Pr:%protection\n  S:%speed Po:%potency T:%tenacity\n'

MODSET_OPTS = {
	'he':              'Health',
	'health':          'Health',
	'de':              'Defense',
	'defense':         'Defense',
	'po':              'Potency',
	'potency':         'Potency',
	'te':              'Tenacity',
	'tenacity':        'Tenacity',
	'cc':              'Critical Chance',
	'critical-chance': 'Critical Chance',
	'cd':              'Critical Damage',
	'critical-damage': 'Critical Damage',
	'of':              'Offense',
	'offense':         'Offense',
	'sp':              'Speed',
	'speed':           'Speed',
}

MODSHAPE_OPTS = {
	'sq':       'Square',
	'square':   'Square',
	'ar':       'Arrow',
	'arrow':    'Arrow',
	'di':       'Diamond',
	'diamond':  'Diamond',
	'tr':       'Triangle',
	'triangle': 'Triangle',
	'ci':       'Circle',
	'circle':   'Circle',
	'cr':       'Cross',
	'cross':    'Cross',
}

def parse_opts_format(config, args):

	args_cpy = list(args)

	for arg in args_cpy:
		if arg in config['formats']:
			args.remove(arg)
			return args, config['formats'][arg]

	return args, DEFAULT_FORMAT

def parse_opts_ally_codes(config, author, args):

	ally_codes = []
	args_cpy = list(args)

	for arg in args_cpy:

		if len(arg) >= 9 and arg.isdigit():
			args.remove(arg)
			ally_codes.append(arg)

	if not ally_codes and author in config['allies']['by-discord-nick']:
		ally_codes.append(config['allies']['by-discord-nick'][author][2])

	return args, ally_codes

def parse_opts_unit_names(config, args, combat_type=1):

	selected_units = []
	new_args = list(args)

	for arg in new_args:

		if len(arg) < 2:
			continue

		larg = basicstrip(arg)
		if larg in config['nicks']:
			larg = basicstrip(config['nicks'][larg])

		found = False
		units = get_all_units()

		for base_id, unit in units.items():

			if unit['combat_type'] != combat_type:
				continue

			name1 = basicstrip(unit['name'])
			name2 = name1.replace('î', 'i').replace('Î', 'i')
			name3 = name1.replace('-', '')
			name4 = name1.replace('\'', '')

			if larg in name1 or larg in name2 or larg in name3 or larg in name4:
				found = True
				selected_units.append(unit)
				if larg == name1:
					break

		if found:
			args.remove(arg)

	return args, selected_units

def parse_opts_modsets(args):

	selected_modsets = []
	args_cpy = list(args)
	for arg in args_cpy:
		if arg in MODSET_OPTS:
			args.remove(arg)
			modset = MODSET_OPTS[arg]
			if modset not in selected_modsets:
				selected_modsets.append(modset)

	return args, selected_modsets

def parse_opts_modshapes(args):

	selected_modshapes = []
	args_cpy = list(args)
	for arg in args_cpy:
		if arg in MODSHAPE_OPTS:
			args.remove(arg)
			modshape = MODSHAPE_OPTS[arg]
			if modshape not in selected_modshapes:
				selected_modshapes.append(modshape)

	return args, selected_modshapes
