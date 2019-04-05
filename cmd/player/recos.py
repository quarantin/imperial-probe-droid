#!/usr/bin/python3

from opts import *
from utils import basicstrip, get_mod_sets_emojis, get_mod_primaries, get_field_legend
from constants import EMOJIS, SHORT_STATS

from swgohgg import get_char_list, get_avatar_url, get_full_avatar_url
from swgohhelp import fetch_players

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
	emoji_gg = EMOJIS['swgoh.gg']

	args, ally_codes = parse_opts_ally_codes(config, author, args)
	if not ally_codes:
		return [{
			'title': 'Error: Not Found',
			'color': 'red',
			'description': 'No ally code specified or found registered to %s' % author,
		}]

	args, selected_units = parse_opts_unit_names(config, args)
	if not selected_units:
		return [{
			'title': 'Error: No Units Selected',
			'color': 'red',
			'description': 'You have to provide at least one unit name.\nPlease check %shelp recos for more information.' % config['prefix'],
		}]

	if args:
		plural = len(args) > 1 and 's' or ''
		return [{
			'title': 'Error: Unknown Parameter%s' % plural,
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
		}]

	players = fetch_players(config, ally_codes)

	msgs = []
	for ally_code in ally_codes:

		discord_id = None
		if ally_code in config['allies']['by-ally-code']:
			discord_id = config['allies']['by-ally-code'][ally_code][1]

		for ref_unit in selected_units:

			name    = ref_unit['name']
			base_id = ref_unit['base_id']
			roster  = players[ally_code]['roster']
			if name in config['recos']['by-name']:
				recos = config['recos']['by-name'][name]
				lines = []

				for reco in recos:

					source   = EMOJIS[ reco['source'].replace(' ', '').lower() ]

					set1     = EMOJIS[ reco['set1'].replace(' ', '').lower() ]
					set2     = EMOJIS[ reco['set2'].replace(' ', '').lower() ]
					set3     = EMOJIS[ reco['set3'].replace(' ', '').lower() ]

					square   = SHORT_STATS[ reco['square'].strip()   ]
					arrow    = SHORT_STATS[ reco['arrow'].strip()    ]
					diamond  = SHORT_STATS[ reco['diamond'].strip()  ]
					triangle = SHORT_STATS[ reco['triangle'].strip() ]
					circle   = SHORT_STATS[ reco['circle'].strip()   ]
					cross    = SHORT_STATS[ reco['cross'].strip()    ]

					info     = reco['info'].strip()
					info     = info and ' %s' % info or ''

					line = '%s%s%s%s`%s|%s|%s|%s`%s' % (source, set1, set2, set3, arrow, triangle, circle, cross, info)
					lines.append(line)

				if base_id in roster and 'mods' in roster[base_id]:
					unit = roster[base_id]
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

				elif base_id not in roster:
					unit = None
					line = '%s is still locked for %s' % (ref_unit['name'], discord_id or ally_code)

				else:
					unit = roster[base_id]
					line = '%s has no mods for %s' % (ref_unit['name'], discord_id or ally_code)

				lines.append(config['separator'])
				lines.append(line)

				spacer = EMOJIS[''] * 4

				line = '%s%s%s%s%s' % (spacer, EMOJIS['arrow'], EMOJIS['triangle'], EMOJIS['circle'], EMOJIS['cross'])
				lines = [ line ] + lines

				field_legend = get_field_legend(config)

				msgs.append({
					'title': '== Recommended Mod Sets and Primary Stats ==',
					'description': '\n'.join(lines),
					'author': {
						'name': ref_unit['name'],
						'icon_url': get_avatar_url(base_id),
					},
					'image': get_full_avatar_url(config, ref_unit['image'], unit),
					'fields': [ field_legend ],
				})
			else:
				msgs.append({
					'title': '== No Recommended Mod Sets ==',
					'description': '%s is missing from the recommendation spreadsheet' % ref_unit['name'],
				})

	return msgs
