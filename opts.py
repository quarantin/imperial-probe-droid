import re

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

def parse_opts_ally_code(arg):
	regex = r'^[0-9]{9}$|^[0-9]{3}-[0-9]{3}-[0-9]{3}$'
	m = re.search(regex, arg)
	return m and int(m.group(0).replace('-', '')) or False

def parse_opts_ally_codes(config, author, args):

	ally_codes = []
	args_cpy = list(args)
	for arg in args_cpy:

		ally_code = parse_opts_ally_code(arg)
		if ally_code:
			args.remove(arg)
			ally_codes.append(ally_code)

	return list(set(ally_codes))

def parse_opts_mentions(config, author, args):

	discord_ids = []
	args_cpy = list(args)
	for arg in args_cpy:

		discord_id = None

		m = re.search(r'^<@([0-9]+)>$', arg)
		if m:
			args.remove(arg)
			discord_ids.append(int(m.group(1)))

		elif arg.lower() in [ 'me', '@me' ]:
			args.remove(arg)
			discord_ids.append(author.id)

		else:
			p = Player.get_player_by_nick(arg)
			if p:
				args.remove(arg)
				discord_ids.append(p.discord_id)

	return list(set(discord_ids))

def parse_opts_players(config, author, args, min_allies=1, max_allies=-1, expected_allies=1, language='eng_us'):

	discord_ids = parse_opts_mentions(config, author, args)
	ally_codes = parse_opts_ally_codes(config, author, args)

	unregistered = []
	for discord_id in discord_ids:

		try:
			p = Player.objects.get(discord_id=discord_id)
			if p.ally_code not in ally_codes:
				ally_codes.append(p.ally_code)

		except Player.DoesNotExist:
			unregistered.append(discord_id)

	if unregistered:
		return args, None, error_ally_codes_not_registered(config, unregistered)

	if (not discord_ids and not ally_codes) or len(ally_codes) < min_allies or len(ally_codes) < expected_allies:
		try:
			p = Player.objects.get(discord_id=author.id)
			if p.ally_code not in ally_codes:
				ally_codes.insert(0, p.ally_code)

		except Player.DoesNotExist:
			pass

	if not ally_codes:
		return args, None, error_no_ally_code_specified(config, author)

	if len(ally_codes) < min_allies:
		return args, None, error_not_enough_ally_codes_specified(ally_codes, min_allies)

	if len(ally_codes) > max_allies and max_allies != -1:
		return args, None, error_too_many_ally_codes_specified(ally_codes, max_allies)

	players = []
	for ally_code in ally_codes:
		try:
			p = Player.objects.get(ally_code=ally_code)
			if p not in players:
				players.append(p)

		except Player.DoesNotExist:
			p = Player(ally_code=ally_code)
			if p not in players:
				players.append(p)

	return args, players, None

def parse_opts_unit_names_by_faction(config, arg):

	faction = []

	larg = basicstrip(arg.lower())
	if larg in BaseUnitFaction.FACTION_NICKS:
		larg = BaseUnitFaction.FACTION_NICKS[larg]

	for fac_key, fac_name in BaseUnitFaction.FACTIONS:
		if larg in fac_key.split('_'):
			if fac_key not in faction:
				faction.append(fac_key)
			break

	return BaseUnit.get_units_by_faction(faction)

def parse_opts_unit_names_broad(config, args, units):

	full_match = []
	token_match = []
	wild_match = []
	loose_match = []

	if not args:
		return None

	arg = basicstrip(' '.join(args))

	faction = parse_opts_unit_names_by_faction(config, arg)
	if faction:
		return faction

	for unit in units:

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

def parse_opts_unit_names(config, args):

	if not args:
		return args, []

	units = BaseUnit.objects.all()

	match = parse_opts_unit_names_broad(config, args, units)
	if match:
		args.clear()
		return args, match

	selected_units = []
	args_cpy = list(args)

	for arg in args_cpy:

		nick = basicstrip(arg)
		if nick in config['nicks']:
			nick = basicstrip(config['nicks'][nick])

		match = parse_opts_unit_names_broad(config, [ nick ], units)
		if match:
			args.remove(arg)
			for m in match:
				if m not in selected_units:
					selected_units.append(m)

	return args, selected_units

def parse_opts_unit_names_v1(config, args):

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
		'gp':     1,
		'gear':   1,
		'level':  1,
		'rarity': 1,
	}

	rules = {
		'gp':     r'^(gp)([0-9]+)$',
		'gear':   r'^(g|gear[s]{0,1})([0-9]+)$',
		'level':  r'^(l|level[s]{0,1})([0-9]+)$',
		'rarity': r'^(s|star[s]{0,1})([0-9]+)$',
	}

	args_cpy = list(args)
	for arg in args_cpy:
		for key, regex in rules.items():
			m = re.search(regex, arg)
			if m:
				args.remove(arg)
				selected_char_filters[key] = int(m.group(2))

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

	args_cpy = list(args)
	for arg in args_cpy:

		argl = arg.lower()
		language = Player.get_language_info(argl)
		if language is not None:
			args.remove(arg)
			return args, language

	return args, None
