from opts import *
from errors import *
from swgohgg import get_swgohgg_player_unit_url
from swgohhelp import fetch_players, get_unit_name
from constants import MODSETS_NEEDED

help_modcheck = {
	'title': 'Modcheck Help',
	'description': """Shows weak mod setups for the supplied ally codes.

**Syntax**
```
%prefixmodcheck [ally_codes or mentions] [options]```
**Aliases**
```
%prefixmc```
**Options**
**`missing`** (or **`m`**): To show units with missing mods.
**`nomods`** (or **`n`**): To show units with no mods.
**`incomplete`** (or **`i`**): To show units with incomplete modsets.
**`level`** (or **`l`**): To show units with mods less than level 15.
**`5pips`** (or **`5`**): To show units with mods less than 5 pips.
**`6pips`** (or **`6`**): To show units with mods less than 6 pips.
**`tier`** (or **`t`**): To show units with mods less than gold quality.
If no options is specified, the following options will be selected by default:
Missing, nomods, incomplete, level and 5pips.

**Examples**
```
%prefixmc
%prefixmc @Someone
%prefixmc 123456789 missing
%prefixmc nomods
%prefixmc incomplete```""",
}

MAX_MOD_LEVEL = 15
MAX_MODS_PER_UNIT = 6
MIN_LEVEL_FOR_MODS = 50

def parse_opts_actions(request):

	actions = []
	args = request.args
	args_cpy = list(args)
	for arg in args_cpy:

		larg = arg.lower()

		if larg in [ 'c', 'count' ]:
			args.remove(arg)
			actions.append('count')

		elif larg in [ 'm', 'miss', 'missing' ]:
			args.remove(arg)
			actions.append('missing')

		elif larg in [ 'n', 'nm', 'nomods' ]:
			args.remove(arg)
			actions.append('missing')

		elif larg in [ 'i', 'inc', 'incomplete' ]:
			args.remove(arg)
			actions.append('incomplete')

		elif larg in [ 'l', 'lvl', 'level' ]:
			args.remove(arg)
			actions.append('level')

		elif larg in [ '5', '5p', '5pip', '5pips', '5-pips' ]:
			args.remove(arg)
			actions.append('5pips')

		elif larg in [ '6', '6p', '6pip', '6pips', '6-pips' ]:
			args.remove(arg)
			actions.append('6pips')

		elif larg in [ 't', 'tier', 'tiers', 'color' ]:
			args.remove(arg)
			actions.append('tier')

	return actions

def get_mod_stats(roster):

	modcount = 0
	units_with_no_mods = []
	units_with_missing_mods = []
	units_with_incomplete_modsets = []
	units_with_incomplete_modlevels = []
	units_with_mods_less_5_pips = []
	units_with_mods_less_6_pips = []
	units_with_mods_weak_tier = []

	for base_id, unit in roster.items():

		if unit['combatType'] != 1 or unit['level'] < MIN_LEVEL_FOR_MODS:
			continue

		unit['weak-tier'] = []
		unit['mods-not-5-pips'] = []
		unit['mods-not-6-pips'] = []
		unit['mods-no-max-level'] = []

		modcount += len(unit['mods'])

		if not unit['mods']:
			units_with_no_mods.append(unit)
			continue

		unit['missing-mods'] = MAX_MODS_PER_UNIT - len(unit['mods'])
		if unit['missing-mods'] > 0:
			units_with_missing_mods.append(unit)

		modsets = {}
		for mod in unit['mods']:

			if mod['pips'] < 5:
				unit['mods-not-5-pips'].append(mod)
				if unit not in units_with_mods_less_5_pips:
					units_with_mods_less_5_pips.append(unit)

			if mod['pips'] < 6:

				if mod['tier'] < 5:
					unit['weak-tier'].append(mod)
					if unit not in units_with_mods_weak_tier:
						units_with_mods_weak_tier.append(unit)

				unit['mods-not-6-pips'].append(mod)
				if unit not in units_with_mods_less_6_pips:
					units_with_mods_less_6_pips.append(unit)

			if mod['level'] < MAX_MOD_LEVEL:
				unit['mods-no-max-level'].append(mod)
				if unit not in units_with_incomplete_modlevels:
					units_with_incomplete_modlevels.append(unit)

			modset = mod['set']
			if modset not in modsets:
				modsets[modset] = 0

			modsets[modset] += 1

		for modset, count in modsets.items():
			needed = MODSETS_NEEDED[modset]
			if count % needed != 0 and unit not in units_with_missing_mods:
				units_with_incomplete_modsets.append(unit)
				break

	return modcount, units_with_no_mods, units_with_missing_mods, units_with_incomplete_modsets, units_with_incomplete_modlevels, units_with_mods_less_5_pips, units_with_mods_less_6_pips, units_with_mods_weak_tier

default_actions = [
	'count',
	'missing',
	'nomods',
	'incomplete',
	'level',
	'5pips',
	#'6pips',
	#'tier',
]
def cmd_modcheck(request):

	args = request.args
	author = request.author
	channel = request.channel
	config = request.config

	msgs = []
	units_with_missing_mods = []
	units_with_incomplete_modsets = []

	language = parse_opts_lang(request)

	actions = parse_opts_actions(request)
	if not actions:
		actions = default_actions

	selected_players, error = parse_opts_players(request)

	if error:
		return error

	if not selected_players:
		return error_no_ally_code_specified(config, author)

	if args:
		return error_unknown_parameters(args)

	ally_codes = [ p.ally_code for p in selected_players ]
	players = fetch_players(config, {
		'allycodes': ally_codes,
		'project': {
			'allyCode': 1,
			'name': 1,
			'roster': {
				'defId': 1,
				'level': 1,
				'mods': 1,
				'combatType': 1,
			},
		},
	})

	for ally_code_str, player in players.items():

		lines = []
		roster = player['roster']

		modcount, units_with_no_mods, units_with_missing_mods, units_with_incomplete_modsets, units_with_incomplete_modlevels, units_with_mods_less_5_pips, units_with_mods_less_6_pips, units_with_mods_weak_tier = get_mod_stats(roster)

		if 'count' in actions:
			lines.append('**%d** equipped mods.' % modcount)
			lines.append(config['separator'])

		if 'nomods' in actions:

			sublines = []
			for unit in units_with_no_mods:
				unit_name = get_unit_name(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code_str, unit['defId'])
				sublines.append('**[%s](%s)** (No mods)' % (unit_name, unit_url))
			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		if 'missing' in actions:

			sublines = []
			for unit in units_with_missing_mods:
				unit_name = get_unit_name(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code_str, unit['defId'])
				sublines.append('**[%s](%s)** (**%d** missing)' % (unit_name, unit_url, unit['missing-mods']))
			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		if 'incomplete' in actions:

			sublines = []
			for unit in units_with_incomplete_modsets:
				unit_name = get_unit_name(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code_str, unit['defId'])
				sublines.append('**[%s](%s)** (Incomplete modset)' % (unit_name, unit_url))
			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		if 'level' in actions:

			sublines = []
			for unit in units_with_incomplete_modlevels:
				unit_name = get_unit_name(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code_str, unit['defId'])
				plural = len(unit['mods-no-max-level']) > 1 and 's' or ''
				sublines.append('**[%s](%s)** (**%d** mod%s < L15)' % (unit_name, unit_url, len(unit['mods-no-max-level']), plural))
			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		if '5pips' in actions:

			sublines = []
			for unit in units_with_mods_less_5_pips:
				unit_name = get_unit_name(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code_str, unit['defId'])
				plural = len(unit['mods-not-5-pips']) > 1 and 's' or ''
				sublines.append('**[%s](%s)** (**%d** mod%s < 5 pips)' % (unit_name, unit_url, len(unit['mods-not-5-pips']), plural))
			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		if '6pips' in actions:

			sublines = []
			for unit in units_with_mods_less_6_pips:
				unit_name = get_unit_name(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code_str, unit['defId'])
				plural = len(unit['mods-not-6-pips']) > 1 and 's' or ''
				sublines.append('**[%s](%s)** (**%d** mod%s < 6 pips)' % (unit_name, unit_url, len(unit['mods-not-6-pips']), plural))
			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		if 'tier' in actions:

			sublines = []
			for unit in units_with_mods_weak_tier:
				unit_name = get_unit_name(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code_str, unit['defId'])
				plural = len(unit['weak-tier']) > 1 and 's' or ''
				sublines.append('**[%s](%s)** (**%d** mod%s < Gold)' % (unit_name, unit_url, len(unit['weak-tier']), plural))
			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		lines = lines[0:-1]

		msgs.append({
			'title': '%s' % player['name'],
			'description': '\n'.join(lines),
		})

	return msgs
