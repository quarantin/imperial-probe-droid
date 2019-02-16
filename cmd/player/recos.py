#!/usr/bin/python3

from opts import *
from utils import basicstrip, get_mod_sets_emojis, get_mod_primaries
from constants import EMOJIS, SHORT_STATS

from swgohgg import get_char_list, get_avatar_url, get_full_avatar_url
from swgohhelp import fetch_players, fetch_units

help_recos = {
	'title': 'Recommendations Help',
	'description': """Shows recommended mods from Capital Games and Crouching Rancor.

**Syntax**
```
%prefixrecos [players] [characters]```
**Aliases**
```
%prefixr```
**Examples**
Show recommended mods for **Emperor Palpatine**:
```
%prefixr ep```
Or:
```
%prefixr "emperor palpatine"```
Show recommended mods for **Grand Admiral Thrawn**, **Grand Master Yoda**, **Qui-Gon Jinn**, **General Kenobi**, and **Darth Traya**:
```
%prefixr gat gmy qgj gk traya```
Show recommended mods for **Death Trooper**:
```
%prefixr deathtrooper```
Or:
```
%prefixr "death trooper"```
Show recommended mods for **Darth Traya** on someone by mention:
```
%prefixr @Someone traya```
Show recommended mods for **Darth Nihilus** on two players by ally code:
```
%prefixr 123456789 234567891 nih```"""
}

def cmd_recos(config, author, channel, args):

	emoji_cg = EMOJIS['capitalgames']
	emoji_cr = EMOJIS['crouchingrancor']

	args, ally_codes = parse_opts_ally_codes(config, author, args)
	if not ally_codes:
		return [{
			'title': 'Not Found',
			'color': 'red',
			'description': 'No ally code specified or found registered to %s' % author,
		}]

	args, selected_units = parse_opts_unit_names(config, args)
	if not selected_units:
		return [{
			'title': 'No Units Selected',
			'color': 'red',
			'description': 'You have to provide at least one unit name or a mod filter.\nPlease check %shelp recos for more information.' % config['prefix'],
		}]

	if args:
		plural = len(args) > 1
		return [{
			'title': 'Unknown Parameter%s' % plural,
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
		}]

	ref_units = get_char_list()
	players = fetch_players(config, ally_codes)
	units = fetch_units(config, ally_codes)

	msgs = []
	for ally_code in ally_codes:

		discord_id = None
		if ally_code in config['allies']['by-ally-code']:
			discord_id = config['allies']['by-ally-code'][ally_code][1]

		for ref_unit in selected_units:

			base_id = ref_unit['base_id']
			unit = players[int(ally_code)]['roster-by-id'][base_id]
			unit_name = basicstrip(ref_unit['name'])
			if unit_name in config['recos']['by-name']:
				recos = config['recos']['by-name'][unit_name]
				lines = []

				for reco in recos:

					source   = EMOJIS[ reco[1].replace(' ', '').lower() ]

					info     = reco[2].strip()

					set1     = EMOJIS[ reco[3].replace(' ', '').lower() ]
					set2     = EMOJIS[ reco[4].replace(' ', '').lower() ]
					set3     = EMOJIS[ reco[5].replace(' ', '').lower() ]

					square   = SHORT_STATS[ reco[6].strip()  ]
					arrow    = SHORT_STATS[ reco[7].strip()  ]
					diamond  = SHORT_STATS[ reco[8].strip()  ]
					triangle = SHORT_STATS[ reco[9].strip()  ]
					circle   = SHORT_STATS[ reco[10].strip() ]
					cross    = SHORT_STATS[ reco[11].strip() ]

					info = info and ' %s' % info or ''

					line = '%s%s%s%s`%s|%s|%s|%s`%s' % (source, set1, set2, set3, arrow, triangle, circle, cross, info)
					lines.append(line)

				if 'mods' in unit:
					spacer = EMOJIS['']
					modsets = get_mod_sets_emojis(config, unit['mods'])
					primaries = get_mod_primaries(config, unit['mods'])
					del(primaries[1])
					del(primaries[3])

					primaries = [ primaries[x] for x in primaries ]

					source   = EMOJIS['crimsondeathwatch']

					info     = ' %s' % (discord_id or ally_code)

					set1     = modsets[0]
					set2     = modsets[1]
					set3     = modsets[2]

					short_primaries = []
					for primary in primaries:
						short_primaries.append(SHORT_STATS[primary])

					primaries = '|'.join(short_primaries)

					line = '%s%s%s%s`%s`%s' % (source, set1, set2, set3, primaries, info)

				else:
					line = '%s has no mods (%s)' % (ref_unit['name'], discord_id or ally_code)

				lines.append(config['separator'])
				lines.append(line)

				spacer = EMOJIS[''] * 4

				line = '%s%s%s%s%s' % (spacer, EMOJIS['arrow'], EMOJIS['triangle'], EMOJIS['circle'], EMOJIS['cross'])
				lines = [ line ] + lines

				msgs.append({
					'title': '== Recommended Mod Sets and Primary Stats ==',
					'description': '\n'.join(lines),
					'author': {
						'name': ref_unit['name'],
						'icon_url': get_avatar_url(ref_unit['base_id']),
					},
					'image': get_full_avatar_url(ref_unit['image'], units[int(ally_code)][base_id]),
					'fields': [{
						'name': '== Legend ==',
						'value': '\u202F%s EA / Capital Games\n\u202F%s Crouching Rancor\n%s' % (emoji_cg, emoji_cr, config['separator']),
						'inline': True,
					}]
				})
			else:
				msgs.append({
					'title': 'No Recommended Mod Sets',
					'color': 'red',
					'description': '%s is missing from the recommendation spreadsheet' % ref_unit['name'],
				})

	return msgs
