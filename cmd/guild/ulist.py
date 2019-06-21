from opts import *
from errors import *

from utils import get_star
from swgohhelp import fetch_players, fetch_guilds

help_unit_list = {
	'title': 'Unit List Help',
	'description': """List your guild members matching some character requirements.

**Syntax**
```
%prefixulist [players] [filters]```
**Options**
Possible filters are:
**`gp<number>`**: To filter units by GP.
**`gear<number>`** or **`g<number>`**: To filter units by gear level.
**`level<number>`** or **`l<number>`**: To filter units by level.
**`star<number>`** or **`s<number>`**: To filter units by rarity.

**Examples**
Search your guild for all separatists units at least Gear 12:
```
%prefixulist separatist g12```"""
}

def unit_is_matching(unit, char_filters):

	if unit['gp'] < char_filters['gp']:
		return False

	if unit['gear'] < char_filters['gear']:
		return False

	if unit['level'] < char_filters['level']:
		return False

	if unit['rarity'] < char_filters['rarity']:
		return False

	return True

def cmd_unit_list(config, author, channel, args):

	lang = parse_opts_lang(author)

	args, selected_char_filters = parse_opts_char_filters(args)

	args, selected_players, error = parse_opts_players(config, author, args)

	args, selected_units = parse_opts_unit_names(config, args)

	if error:
		return error

	if not selected_players:
		return error_no_ally_code_specified(config, author)

	if not selected_units:
		return error_no_unit_selected()

	if args:
		return error_unknown_parameters(args)

	fields = []
	ally_codes = [ p.ally_code for p in selected_players ]
	unit_list = fetch_guilds(config, {
		'allycodes': [ str(x) for x in ally_codes ],
		'project': {
			'guildName': 1,
			'roster': {
				'allyCode': 1,
			}
		},
	})

	for root_ally_code, guild in unit_list.items():
		for ally_code, player in guild['roster'].items():
			if int(player['allyCode']) not in ally_codes:
				ally_codes.append(int(player['allyCode']))

	players = fetch_players(config, {
		'allycodes': ally_codes,
		'project': {
			'name': 1,
			'allyCode': 1,
			'guildName': 1,
			'roster': {
				'defId': 1,
				'gp': 1,
				'gear': 1,
				'level': 1,
				'rarity': 1,
			},
		},
	})

	images = {}
	matches = {}
	for ally_code, player in players.items():
		guild_name = player['guildName']
		player_name = player['name']
		for ref_unit in selected_units:

			if guild_name not in matches:
				matches[guild_name] = {}

			if player_name not in matches[guild_name]:
				matches[guild_name][player_name] = {}

			base_id = ref_unit.base_id
			if base_id not in player['roster']:
				#print('Unit is locked for: %s' % player_name)
				continue

			unit = player['roster'][base_id]
			if not unit_is_matching(unit, selected_char_filters):
				#print('Unit does not match criteria for: %s' % player_name)
				continue

			images[ref_unit.name] = ref_unit.get_image()
			matches[guild_name][player_name][ref_unit.name] = {
				'gp':      unit['gp'],
				'gear':    unit['gear'],
				'level':   unit['level'],
				'rarity':  unit['rarity'],
				'base_id': ref_unit.base_id,
				'name':    ref_unit.name,
			}

	msgs = []
	for guild_name, player_names in matches.items():
		for player_name, units in player_names.items():

			lines = []
			lines.append(config['separator'])
			#lines.append('`|%s| GP\u00a0 |Lv|GL|Player`' % get_star())
			lines.append('`|%s| GP\u00a0 |Lv|GL|Unit`' % '*')

			rosters = sorted(units.items(), key=lambda x: x[1]['gp'], reverse=True)
			for unit_name, unit in rosters:
				pad_gp = (5 - len(str(unit['gp']))) * '\u00a0'
				pad_gear = (2 - len(str(unit['gear']))) * '\u00a0'
				pad_level = (2 - len(str(unit['level']))) * '\u00a0'
				lines.append('`|%s|%s%d|%s%d|%s%d|`**`%s`**' % (unit['rarity'], pad_gp, unit['gp'], pad_level, unit['level'], pad_gear, unit['gear'], unit['name']))

			if not len(units):
				lines.append('No unit found matching the search criteria.')

			msgs.append({
				'title': '%s (%d)' % (player_name, len(units)),
				'description': '\n'.join(lines),
			})

	if not msgs:
		msgs.append({
			'title': 'No Matching Unit',
			'description': 'No player found with characters matching your search criteria.',
		})

	return msgs
