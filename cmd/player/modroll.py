from opts import *
from errors import *
from utils import translate
from swgohhelp import fetch_players, get_unit_name
from constants import MODSLOTS, MODSETS, MODSECONDARYSTATS, EMOJIS

help_modroll= {
	'title': 'Modroll Help',
	'description': """List equipped mods having a secondary stat with 5 rolls.

**Syntax**
```
%prefixmodroll [players]```
**Aliases**
```
%prefixmr```
**Examples**
```
%prefixmodroll
%prefixmr```"""
}

MIN_ROLLS = 5

MOD_STATS = {
	5:  'speed',
	41: 'offense',
}

def cmd_modroll(config, author, channel, args):

	msgs = []

	language = parse_opts_lang(author)

	args, selected_players, error = parse_opts_players(config, author, args)
	if args:
		return error_unknown_parameters(args)

	if error:
		return error

	if not selected_players:
		return error_no_ally_code_specified(config, author)

	ally_codes = [ p.ally_code for p in selected_players ]

	data = fetch_players(config, {
		'allycodes': ally_codes,
		'project': {
			'allyCode': 1,
			'name': 1,
			'roster': {
				'defId': 1,
				'mods': 1,
			},
		},
	})

	players = {}
	for ally_code_str, player in data.items():
		ally_code = player['allyCode']
		players[ally_code] = player

	result = {}
	for ally_code, player in players.items():
		player_name = player['name']
		for def_id, unit in player['roster'].items():
			unit_name = get_unit_name(config, def_id, language)
			for mod in unit['mods']:
				for sec_stat in mod['secondaryStat']:
					if sec_stat['roll'] >= MIN_ROLLS:

						if player_name not in result:
							result[player_name] = {}

						if unit_name not in result[player_name]:
							result[player_name][unit_name] = []

						result[player_name][unit_name].append(mod)

	msgs = []
	for player_name, data in result.items():
		lines = []
		for unit_name, mods in sorted(data.items()):
			lines.append(unit_name)
			for mod in mods:
				slot = MODSLOTS[ mod['slot'] ].replace(' ', '').lower()
				slot_emoji = EMOJIS[slot]
				modset = MODSETS[ mod['set'] ].replace(' ', '').lower()
				modset_emoji = EMOJIS[modset]
				for sec in mod['secondaryStat']:
					if sec['roll'] >= MIN_ROLLS:
						stat_name = MODSECONDARYSTATS[ sec['unitStat'] ]
						stat_value = ('%.2f' % sec['value']).replace('.00', '')
						lines.append('%s%s %dD (%d) +%s %s' % (modset_emoji, slot_emoji, mod['pips'], sec['roll'], stat_value, stat_name))
		msgs.append({
			'title': '%d Roll Mods of %s' % (MIN_ROLLS, player_name),
			'description': '\n'.join(lines),
		})

	return msgs
