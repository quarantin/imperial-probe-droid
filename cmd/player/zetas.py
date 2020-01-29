from opts import *
from errors import *
from utils import http_get, translate

from swgohgg import get_full_avatar_url
from swgohhelp import fetch_players

import DJANGO
from swgoh.models import BaseUnitGear

help_zetas = {
	'title': 'Zetas Help',
	'description': """Shows most popular zetas that you don't already have.

**Syntax**
```
%prefixzetas [player]```
**Aliases**
```
%prefixz```

**Examples**
```
%prefixz```"""
}

def cmd_zetas(request):

	args = request.args
	author = request.author
	config = request.config

	language = parse_opts_lang(request)

	selected_players, error = parse_opts_players(request, min_allies=1, max_allies=1)

	selected_units = parse_opts_unit_names(request)

	if error:
		return error

	if not selected_players:
		return error_no_ally_code_specified(config, author)

	if not selected_units:
		return error_no_unit_selected()

	if args:
		return error_unknown_parameters(args)

	ally_code = selected_players[0].ally_code
	players = fetch_players(config, {
		'allycodes': [ ally_code ],
		'project': {
			'allyCode': 1,
			'name': 1,
			'roster': {
				'defId': 1,
				'gear': 1,
				'level': 1,
				'rarity': 1,
				'relic': 1,
				'skills': 1,
				'equipped': {
					'slot': 1,
				},
			},
		},
	})


	msgs = []
	player = players[ally_code]
	for unit in selected_units:

		lines = []
		fields = []
		player_unit = unit.base_id in player['roster'] and player['roster'][unit.base_id] or {}
		json = get_gear_levels(unit.base_id)
		for name, data in json.items():
			unit_name = translate(unit.base_id, language)
			lines.append('**[%s](%s)**' % (unit_name, unit.get_url()))
			min_gear_level = player_unit and player_unit['gear'] or 1
			for tier in reversed(range(min_gear_level, 13)):
				sublines = []
				for slot in sorted(data['tiers'][tier]):
					gear_id = data['tiers'][tier][slot]['gear']
					gear_url = data['tiers'][tier][slot]['url']
					gear_name = translate(gear_id, language)
					equipped = False
					if player_unit:
						for gear in player_unit['equipped']:
							if tier == player_unit['gear']:
								# gear['slot'] is an index, so add one for comparison
								if int(slot) == gear['slot'] + 1:
									equipped = True
									break

					bold = not equipped and '**' or ''

					sublines.append('%sSlot%s: [%s](%s)%s' % (bold, slot, gear_name, gear_url, bold))

				gear_tier_id = 'Unit_Tier%02d' % tier
				gear_tier_title = translate(gear_tier_id, language)

				fields.append({
					'name': '== %s ==' % gear_tier_title,
					'value': '\n'.join(sublines),
				})

		if not fields:
			lines.append('Maximum gear level.')

		msgs.append({
			#'title': '== Needed Gear ==',
			'description': '\n'.join(lines),
			'author': {
				'name': unit.name,
				'icon_url': unit.get_image(),
			},
			'image': get_full_avatar_url(config, unit.image, player_unit),
			'fields': fields,
		})

	return msgs
