#!/usr/bin/python3

from opts import *
from utils import basicstrip, get_mod_sets_emojis, get_mod_primaries
from constants import EMOJIS, SHORT_STATS

from swgohgg import get_char_list, get_avatar_url, get_full_avatar_url
from swgohhelp import fetch_players, fetch_units

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

					if prim != reco[5 + slot]:
						continue

					matching_recos.append(reco)

		if not matching_recos:
			desc = 'No matching recommendation for the supplied filters.'
		else:
			lines = []
			for recos in matching_recos:
				char_name = recos[0]
				if char_name not in lines:
					lines.append(char_name)
			modset, modslot, primary = '', '', ''
			desc = '%s%s %s\nHere is the list of characters who need this type of mod:\n - %s' % (modslot, modset, primary, '\n - '.join(lines))

		return [{
			'title': 'Who Needs This Mod',
			'description': desc,
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

			# TODO
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
				lines = [ config['separator'], line ] + lines

				msgs.append({
					'title': 'Recommended Mod Sets and Primary Stats',
					'author': {
						'name': ref_unit['name'],
						'icon_url': get_avatar_url(ref_unit['base_id']),
					},
					'image': get_full_avatar_url(ref_unit['image'], units[int(ally_code)][base_id]),
					'description': '\n'.join(lines),
				})
			else:
				msgs.append({
					'title': 'No Recommended Mod Sets',
					'color': 'red',
					'description': '%s is missing from the recommendation spreadsheet' % ref_unit['name'],
				})

	return msgs
