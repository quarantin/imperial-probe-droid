#!/usr/bin/python3

from utils import basicstrip
from swgohgg import get_unit_list

DEFAULT_FORMAT = '**%name** (%role)\n GP:%gp H:%health Pr:%protection\n  S:%speed Po:%potency T:%tenacity\n'

MODSET_OPTS = {
	'he':             1,
	'health':         1,
	'de':             3,
	'defense':        3,
	'po':             7,
	'potency':        7,
	'te':             8,
	'tenacity':       8,
	'cc':             5,
	'criticalchance': 5,
	'cd':             6,
	'criticaldamage': 6,
	'of':             2,
	'offense':        2,
	'sp':             4,
	'speed':          4,
}

MODSET_OPTS_2 = {
	'he':             'Health',
	'health':         'Health',
	'de':             'Defense',
	'defense':        'Defense',
	'po':             'Potency',
	'potency':        'Potency',
	'te':             'Tenacity',
	'tenacity':       'Tenacity',
	'cc':             'Critical Chance',
	'criticalchance': 'Critical Chance',
	'cd':             'critical Damage',
	'criticaldamage': 'Critical Damage',
	'of':             'Offense',
	'offense':        'Offense',
	'sp':             'Speed',
	'speed':          'Speed',
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

MODPRIMARIES_OPTS = {
	'ac':                'Accuracy',
	'accuracy':          'Accuracy',
	'ca':                'Critical Avoidance',
	'criticalavoidance': 'Critical Avoidance',
	'cc':                'Critical Chance',
	'criticalchance':    'Critical Chance',
	'cd':                'Critical Damage',
	'criticaldamage':    'Critical Damage',
	'de':                'Defense',
	'defense':           'Defense',
	'he':                'Health',
	'health':            'Health',
	'of':                'Offense',
	'offense':           'Offense',
	'po':                'Potency',
	'potency':           'Potency',
	'pr':                'Protection',
	'protection':        'Protection',
	'sp':                'Speed',
	'speed':             'Speed',
	'te':                'Tenacity',
	'tenacity':          'Tenacity',
}

def parse_opts_format(config, args):

	args_cpy = iter(list(args))

	for arg in args_cpy:

		if arg in config['formats']:
			args.remove(arg)
			return args, config['formats'][arg]

		elif arg in [ 'c', 'custom' ]:
			args.remove(arg)
			fmt = next(args_cpy)
			args.remove(fmt)
			return args, fmt

	return args, DEFAULT_FORMAT

def parse_opts_ally_code(config, author, arg):

	if len(arg) >= 11 and arg.find('-') == 3:
		arg = ''.join(arg.split('-'))

	if len(arg) >= 9 and arg.isdigit():
		return arg

	if arg in config['allies']['by-mention']:
		return config['allies']['by-mention'][arg][2]

	return None


def parse_opts_ally_codes(config, author, args, min_allies=1):

	ally_codes = []
	args_cpy = list(args)

	for arg in args_cpy:

		if len(arg) >= 11 and arg.find('-') == 3:
			cpy = ''.join(arg.split('-'))
			if len(cpy) >= 9 and cpy.isdigit():
				args.remove(arg)
				ally_codes.append(cpy)

		elif len(arg) >= 9 and arg.isdigit():
			args.remove(arg)
			ally_codes.append(arg)

		elif arg in config['allies']['by-mention']:
			args.remove(arg)
			ally_codes.append(config['allies']['by-mention'][arg][2])

	if len(ally_codes) < min_allies and author in config['allies']['by-discord-nick']:
		ally_codes.append(config['allies']['by-discord-nick'][author][2])

	return args, ally_codes

def parse_opts_unit_names_broad(config, args, units, combat_type=1):

	full_match = []
	token_match = []
	wild_match = []
	loose_match = []

	arg = basicstrip(' '.join(args))

	for base_id, unit in units.items():

		if unit['combat_type'] != combat_type:
			continue

		if arg in config['nicks']:
			arg = basicstrip(config['nicks'][arg])

		name = basicstrip(unit['name'])

		if arg == name:
			full_match.append(unit)

		elif arg in name.split('-') or arg in name.split(' '):
			token_match.append(unit)

		elif arg in name or arg in name.replace('-', '').replace(' ', ''):
			wild_match.append(unit)

		elif arg.replace('-', '') == name.replace('-', ''):
			loose_match.append(unit)

	if full_match:
		return full_match

	if token_match:
		return token_match

	if wild_match:
		return wild_match

	if loose_match:
		return loose_match

	return None

def parse_opts_unit_names(config, args, combat_type=1):

	if not args:
		return args, []

	units = get_unit_list()

	match = parse_opts_unit_names_broad(config, args, units, combat_type)
	if match:
		args.clear()
		return args, match

	selected_units = []
	args_cpy = list(args)

	for arg in args_cpy:

		nick = basicstrip(arg)
		if nick in config['nicks']:
			nick = basicstrip(config['nicks'][nick])

		match = parse_opts_unit_names_broad(config, [ nick ], units, combat_type)
		if match:
			args.remove(arg)
			for m in match:
				if m not in selected_units:
					selected_units.append(m)

	return args, selected_units

def parse_opts_unit_names_v1(config, args, combat_type=1):

	selected_units = []
	new_args = list(args)

	for arg in new_args:

		if len(arg) < 2:
			continue

		larg = basicstrip(arg)
		if larg in config['nicks']:
			larg = basicstrip(config['nicks'][larg])

		found = False
		units = get_unit_list()

		new_units = []
		for base_id, unit in units.items():

			if unit['combat_type'] != combat_type:
				continue

			name1 = basicstrip(unit['name'])
			name2 = name1.replace('î', 'i').replace('Î', 'i')
			name3 = name1.replace('-', '')
			name4 = name1.replace('\'', '')

			if larg in name1 or larg in name2 or larg in name3 or larg in name4:
				found = True
				new_units.append(unit)
				if larg == name1:
					new_units = [ unit ]
					break

		if found:
			args.remove(arg)
			selected_units.extend(new_units)

	return args, selected_units

def parse_opts_char_filters(args):

	selected_char_filters = {
		'gear': [],
		'level': [],
		'star': [],
	}
	args_cpy = list(args)
	for arg in args_cpy:
		toks = arg.split('=')
		if len(toks) != 2:
			continue

		if toks[0] in [ 'g', 'gear' ] and toks[1].isdigit():
			args.remove(arg)
			selected_char_filters['gear'].append(int(toks[1]))

		elif toks[0] in [ 'l', 'level' ] and toks[1].isdigit():
			args.remove(arg)
			selected_char_filters['level'].append(int(toks[1]))

		elif toks[0] in [ 's', 'star' ] and toks[1].isdigit():
			args.remove(arg)
			selected_char_filters['star'].append(int(toks[1]))

	return args, selected_char_filters

def parse_opts_modsets(args, ref_table):

	selected_modsets = []
	args_cpy = list(args)
	for arg in args_cpy:
		if arg in ref_table:
			args.remove(arg)
			modset = ref_table[arg]
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

def parse_opts_mod_filters(args):

	selected_filters = []
	args_cpy = list(args)
	for arg in args_cpy:
		toks = arg.split('/')
		if len(toks) == 3:
			_, modsets = parse_opts_modsets([ toks[0] ], MODSET_OPTS_2)
			_, slots   = parse_opts_modslots([ toks[1] ])
			_, prims   = parse_opts_modprimaries([ toks[2] ])
			if modsets and slots and prims:
				tupl = (modsets[0], slots[0], prims[0])
				if tupl not in selected_filters:
					args.remove(arg)
					selected_filters.append(tupl)

	return args, selected_filters

def parse_opts_lang(args):

	args_cpy = list(args)
	for arg in args_cpy:

		if arg in [ 'en', 'EN', 'english' ]:
			args.remove(arg)
			return args, 'en'

		if arg in [ 'fr', 'FR', 'french' ]:
			args.remove(arg)
			return args, 'fr'

	return args, 'en'
