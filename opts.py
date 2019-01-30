#!/usr/bin/python3

from utils import basicstrip
from swgoh import get_all_units

DEFAULT_FORMAT = '**%name**%leader%reinforcement\n  P:%power H:%health Pr:%protection\n  S:%speed Po:%potency T:%tenacity\n'

MODSET_OPTS = {
	'he':              1,
	'health':          1,
	'de':              3,
	'defense':         3,
	'po':              7,
	'potency':         7,
	'te':              8,
	'tenacity':        8,
	'cc':              5,
	'critical-chance': 5,
	'cd':              6,
	'critical-damage': 6,
	'of':              2,
	'offense':         2,
	'sp':              4,
	'speed':           4,
}

MODSLOTS_OPTS = {
	'sq':       1,
	'square':   1,
	'ar':       2,
	'arrow':    2,
	'di':       3,
	'diamond':  3,
	'tr':       4,
	'triangle': 4,
	'ci':       5,
	'circle':   5,
	'cr':       6,
	'cross':    6,
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

		if arg in config['allies']['by-mention']:
			args.remove(arg)
			ally_codes.append(config['allies']['by-mention'][arg][2])

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

def parse_opts_modslots(args):

	selected_modslots = []
	args_cpy = list(args)
	for arg in args_cpy:
		if arg in MODSLOTS_OPTS:
			args.remove(arg)
			modslot = MODSLOTS_OPTS[arg]
			if modslot not in selected_modslots:
				selected_modslots.append(modslot)

	return args, selected_modslots

def parse_opts_modprimaries(args):

	selected_primaries = []
	args_cpy = list(args)
	for arg in args_cpy:
		if arg in MODPRIMARIES_OPTS:
			args.remove(arg)
			modprimary = MODPRIMARIES_OPTS[arg]
			if modprimary not in selected_primaries:
				selected_primaries.append(modprimary)

	return args, selected_primaries
