from opts import *
from errors import *
from swgohhelp import fetch_players, get_unit_name
from constants import MODSETS_NEEDED

help_modcheck = {
	'title': 'Mods Help',
	'description': """Shows statistics about mods for the supplied ally codes.

**Syntax**
```
%prefixmods [ally_codes or mentions] [option]```

**Options**
```
missing (or m): To show units with missing mods.
nomods (or n): To show units with no mods.
incomplete (or i): To show units with incomplete modsets.```

**Aliases**
```
%prefixm```

**Examples**
```
%prefixm
%prefixm @Someone
%prefixm 123456789
%prefixm 123456789 missing
%prefixm nomods
%prefixm incomplete```""",
}

MIN_LEVEL_FOR_MODS = 50
MAX_MODS_PER_UNIT = 6

def get_mod_stats(roster):

	modcount = 0
	units_with_no_mods = []
	units_with_missing_mods = []
	units_with_incomplete_modsets = []

	for base_id, unit in roster.items():

		if unit['combatType'] != 1 or unit['level'] < MIN_LEVEL_FOR_MODS:
			continue

		modcount += len(unit['mods'])

		if not unit['mods']:
			units_with_no_mods.append(unit)
			continue

		unit['missing-mods'] = MAX_MODS_PER_UNIT - len(unit['mods'])
		if unit['missing-mods'] > 0:
			units_with_missing_mods.append(unit)
			continue

		modsets = {}
		for mod in unit['mods']:

			modset = mod['set']
			if modset not in modsets:
				modsets[modset] = 0

			modsets[modset] += 1

		for modset, count in modsets.items():
			needed = MODSETS_NEEDED[modset]
			if count % needed != 0:
				units_with_incomplete_modsets.append(unit)
				break

	return modcount, units_with_no_mods, units_with_missing_mods, units_with_incomplete_modsets

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

	return actions

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
		actions = [ 'count', 'missing', 'nomods', 'incomplete' ]

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

		name = player['name']
		roster = player['roster']

		modcount, units_with_no_mods, units_with_missing_mods, units_with_incomplete_modsets = get_mod_stats(roster)

		if 'count' in actions:

			msgs.append({
				'title': '%s\'s Mods' % name,
				'description': '%s has %d equipped mods.' % (name, modcount),
			})

		if 'nomods' in actions:

			lines = []
			for unit in units_with_no_mods:
				unit_name = get_unit_name(config, unit['defId'], language)
				lines.append(' **%s**' % unit_name)

			msgs.append({
				'title': 'Units with no mods for %s' % name,
				'description': '\n'.join(sorted(lines))
			})

		if 'missing' in actions:

			lines = []
			for unit in units_with_missing_mods:
				unit_name = get_unit_name(config, unit['defId'], language)
				lines.append('**`%d`** mods missing for **%s**' % (unit['missing-mods'], unit_name))

			msgs.append({
				'title': 'Units with missing mods for %s' % name,
				'description': '\n'.join(reversed(sorted(lines))),
			})

		if 'incomplete' in actions:
			lines = []
			for unit in units_with_incomplete_modsets:
				unit_name = get_unit_name(config, unit['defId'], language)
				lines.append('**%s**' % unit_name)

			msgs.append({
				'title': 'Units with incomplete modsets for %s' % name,
				'description': '\n'.join(sorted(lines)),
			})

	return msgs
