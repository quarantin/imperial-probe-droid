#!/usr/bin/python3

from opts import *
from utils import basicstrip
from constants import EMOJIS, SHORT_STATS

from swgohgg import get_char_list, get_avatar_url, get_full_avatar_url
from swgohhelp import fetch_players

help_recos = {
	'title': 'Recommendations',
	'description': """Shows recommended mods from Capital Games and Crouching Rancor.

**Syntax**
```
%prefixrecos [ally codes or mentions] [characters]```
**Aliases**
```
%prefixr```
**Examples**
Show recommended mods for **Emperor Palpatine**:
```
%prefixr ep```
or:
```
%prefixr "emperor palpatine"```
Show recommended mods for **Grand Admiral Thrawn**, **Grand Master Yoda**, **Qui-Gon Jinn**, **General Kenobi**, and **Darth Traya**:
```
%prefixr gat gmy qgj gk traya```
Show recommended mods for **Death Trooper**:
```
%prefixr deathtrooper```
or:
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

	args, ally_codes = parse_opts_ally_codes(config, author, args)
	if not ally_codes:
		return [{
			'title': 'Not Found',
			'color': 'red',
			'description': 'No ally code specified, or found registered to <%s>' % author,
		}]

	args, selected_sets = parse_opts_modsets(args, MODSET_OPTS_2)
	args, selected_filters = parse_opts_mod_filters(args)
	args, selected_units = parse_opts_unit_names(config, args)

	if args:
		plural = len(args) > 1
		return [{
			'title': 'Unknown Parameter%s' % plural,
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
		}]

	if not selected_units:

		if not selected_filters:
			return [{
				'title': 'No Units Selected',
				'color': 'red',
				'description': 'You have to provide at least one unit name or a mod filter.\nPlease check %shelp recos for more information.' % config['prefix'],
			}]

		matching_recos = []
		for modset, slot, prim in selected_filters:
			for name, recos in sorted(config['recos']['by-name'].items()):
				for reco in recos:

					alist = [ reco[x] for x in range(3, 6) ]
					if modset not in [ reco[x] for x in range(3, 6) ]:
						continue

					print(reco)
					print('slot: %s, prim: %s, reco[6 + slot] = %s' % (slot, prim, reco[5 + slot]))
					if prim != reco[5 + slot]:
						continue

					matching_recos.append(reco)

		if not matching_recos:
			desc = 'No matching recommendation for the supplied filters.'
		else:
			lines = []
			for recos in matching_recos:
				lines.append('%s' % recos[0])
			modset, modslot, primary = 'blah', 'blah', 'blah'
			desc = '%s%s %s\nHere is the list of characters who need this type of mod:\n - %s' % (modslot, modset, primary, '\n - '.join(lines))

		return [{
			'title': 'Who Needs This Mod',
			'description': desc,
		}]

	ref_units = get_char_list()
	players = fetch_players(config, ally_codes)

	msgs = []
	for ally_code in ally_codes:

		discord_id = None
		if ally_code in config['allies']['by-ally-code']:
			discord_id = config['allies']['by-ally-code'][ally_code][1]

		for unit in selected_units:

			# TODO
			unit = ref_units[ unit['base_id'] ]
			name = basicstrip(unit['name'])
			if name in config['recos']['by-name']:
				recos = config['recos']['by-name'][name]
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

					info = info and ' (%s)' % info or ''

					line = '%s%s%s%s`%s|%s|%s|%s`%s' % (source, set1, set2, set3, arrow, triangle, circle, cross, info)
					lines.append(line)

				if 'modsets' in unit and len(unit['modsets']) > 0:
					source   = EMOJIS['crimsondeathwatch']

					info     = ' %s' % (discord_id or ally_code)

					set1     = EMOJIS[ unit['modsets'][0].replace(' ', '').lower() ]
					set2     = EMOJIS[ unit['modsets'][1].replace(' ', '').lower() ]
					set3     = EMOJIS[ unit['modsets'][2].replace(' ', '').lower() ]

					square   = 1 in unit['mods'] and SHORT_STATS[ unit['mods'][1]['primary_stat']['name'] ] or '??'
					arrow    = 2 in unit['mods'] and SHORT_STATS[ unit['mods'][2]['primary_stat']['name'] ] or '??'
					diamond  = 3 in unit['mods'] and SHORT_STATS[ unit['mods'][3]['primary_stat']['name'] ] or '??'
					triangle = 4 in unit['mods'] and SHORT_STATS[ unit['mods'][4]['primary_stat']['name'] ] or '??'
					circle   = 5 in unit['mods'] and SHORT_STATS[ unit['mods'][5]['primary_stat']['name'] ] or '??'
					cross    = 6 in unit['mods'] and SHORT_STATS[ unit['mods'][6]['primary_stat']['name'] ] or '??'

					line = '%s%s%s%s`%s|%s|%s|%s`%s' % (source, set1, set2, set3, arrow, triangle, circle, cross, info)

				else:
					line = '%s has no mods (%s)' % (unit['name'], discord_id or ally_code)

				lines.append(config['separator'])
				lines.append(line)

				spacer = EMOJIS[''] * 4

				line = '%s%s%s%s%s' % (spacer, EMOJIS['arrow'], EMOJIS['triangle'], EMOJIS['circle'], EMOJIS['cross'])
				lines =  [ config['separator'], line ] + lines

				msgs.append({
					'title': 'Recommended Modsets and Primary Stats',
					'author': {
						'name': unit['name'],
						'icon_url': get_avatar_url(unit['base_id']),
					},
					'image': get_full_avatar_url(config, ally_code, unit['base_id']),
					#'thumbnail': get_full_avatar_url(ally_code, unit['base_id']),
					'description': '\n'.join(lines),
				})
			else:
				msgs.append({
					'title': 'No recommended mods',
					'color': 'red',
					'description': '%s is missing from the recommendation spreadsheet' % unit['name'],
				})

	return msgs
