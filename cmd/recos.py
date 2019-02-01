#!/usr/bin/python3

from opts import *
from swgoh import *
from utils import basicstrip
from constants import EMOJIS, SHORT_STATS

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
```
%prefixr ep
%prefixr gat gmy qgj gk traya
%prefixr deathtrooper
%prefixr @Someone traya
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

	args, selected_units = parse_opts_unit_names(config, args)
	if not selected_units:
		return [{
			'title': 'No Units Selected',
			'color': 'red',
			'description': 'You have to provide at least one unit name.',
		}]

	if args:
		plural = len(args) > 1
		return [{
			'title': 'Unknown parameter%s' % plural,
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
		}]

	msgs = []
	for ally_code in ally_codes:

		discord_id = None
		if ally_code in config['allies']['by-ally-code']:
			discord_id = config['allies']['by-ally-code'][ally_code][1]

		for unit in selected_units:

			unit = get_my_unit_by_id(ally_code, unit['base_id'])
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
					'image': get_full_avatar_url(ally_code, unit['base_id']),
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
