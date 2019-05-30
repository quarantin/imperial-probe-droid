#!/usr/bin/python3

from errors import *
from utils import basicstrip

import DJANGO
from swgoh.models import Player, BaseUnit, BaseUnitFaction

DEFAULT_FORMAT = '**%name** (%role)\n**GP**: %gp **Level**: %level **Gear**: %gear **Health**: %health **Protection**: %protection **Speed**: %speed\n**Potency**: %potency **Tenacity**: %tenacity **CD**: %critical-damage **CC (phy)**: %physical-critical-chance **CC (spe)**: %special-critical-chance\n**Armor**: %armor **Resistance**: %resistance\n'

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

def parse_opts_format(config, opts, args):

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



def parse_opts_ally_codes(config, author, args, min_allies=1):

	ally_codes = []
	args_cpy = list(args)

	for arg in args_cpy:

		ally_code = Player.get_ally_code_by_nick(arg)
		if ally_code:
			args.remove(arg)
			ally_codes.append(ally_code)

		elif len(arg) >= 11 and len(arg.split('-')) == 3:
			cpy = ''.join(arg.split('-'))
			if len(cpy) >= 9 and cpy.isdigit():
				args.remove(arg)
				ally_codes.append(cpy)

		elif len(arg) >= 9 and arg.isdigit():
			args.remove(arg)
			ally_codes.append(arg)

	if len(ally_codes) < min_allies:
		try:
			player = Player.objects.get(discord_id=author.id)
			ally_codes.append(player.ally_code)

		except Player.DoesNotExist:
			pass

	return args, ally_codes

def parse_opts_players(config, author, args, min_allies=1, max_allies=-1, expected_allies=1):

	players = []
	args, ally_codes = parse_opts_ally_codes(config, author, args, min_allies)

	if len(ally_codes) < min_allies or len(ally_codes) < expected_allies:
		try:
			player = Player.objects.get(discord_id=author.id)
			if player.ally_code not in ally_codes:
				ally_codes.insert(0, player.ally_code)
		except Player.DoesNotExist:
			pass

	if not ally_codes:
		return args, None, error_no_ally_code_specified(config, author)

	if len(ally_codes) < min_allies:
		return args, None, error_not_enough_ally_codes_specified(ally_codes, min_allies)

	if len(ally_codes) > max_allies and max_allies != -1:
		return args, None, error_too_many_ally_codes_specified(ally_codes, max_allies)

	for ally_code in ally_codes:
		try:
			player = Player.objects.get(discord_id=author.id, ally_code=ally_code)

		except Player.DoesNotExist:
			player = Player(discord_id=author.id, ally_code=ally_code)
			player.not_in_db = True

		players.append(player)

	return args, players, None

def parse_opts_unit_names_by_faction(config, args):

	factions = []
	args_cpy = list(args)
	for arg in args_cpy:

		larg = arg.lower()
		if larg in BaseUnitFaction.FACTION_NICKS:
			larg = BaseUnitFaction.FACTION_NICKS[larg]

		for fac_key, fac_name in BaseUnitFaction.FACTIONS:
			if larg in fac_key.split('_')[1]:
				args.remove(arg)
				if fac_key not in factions:
					factions.append(fac_key)
				break

	return args, BaseUnit.get_units_by_faction(factions)

def parse_opts_unit_names_broad(config, args, units, combat_type=1):

	full_match = []
	token_match = []
	wild_match = []
	loose_match = []

	args, factions = parse_opts_unit_names_by_faction(config, args)
	if factions:
		return factions

	if not args:
		return None

	arg = basicstrip(' '.join(args))

	for unit in units:

		if int(unit.combat_type) != combat_type:
			continue

		if arg in config['nicks']:
			arg = basicstrip(config['nicks'][arg])

		name = basicstrip(unit.name)

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

	units = BaseUnit.objects.all()

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
		units = BaseUnit.objects.all()

		new_units = []
		for unit in units:

			if unit.combat_type != combat_type:
				continue

			name1 = basicstrip(unit.name)
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

def parse_opts_lang(author):

	try:
		p = Player.objects.get(discord_id=author.id)
		return p.language

	except Player.DoesNotExist:
		pass

	return 'eng_us'

def parse_opts_language(args):

	langs = { lang_code: language for language, lang_code, lang_flag, lang_name in Player.LANGS }

	args_cpy = list(args)
	for arg in args_cpy:

		argl = arg.lower()
		if argl in langs:
			args.remove(arg)
			return args, Player.get_language_info(argl)

	return args, None
