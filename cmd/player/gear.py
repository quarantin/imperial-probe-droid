from opts import *
from errors import *
from utils import http_get, translate

from swgohgg import get_avatar_url
from swgohhelp import fetch_players

help_gear = {
	'title': 'Gear Help',
	'description': """Shows gear needed for a given character.

**Syntax**
```
%prefixgear [unit]```
**Aliases**
```
%prefixg```

**Examples**
Show gear needed for count dooku:
```
%prefixg count dooku```"""
}

def cmd_gear(config, author, channel, args):

	language = parse_opts_lang(author)

	args, selected_players, error = parse_opts_players(config, author, args, min_allies=1, max_allies=1)

	args, units = parse_opts_unit_names(config, args)

	if args:
		return error_unknown_parameters(args)

	if not units:
		return error_no_unit_selected()

	if error:
		return error

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
				'equipped': {
					'slot': 1,
				},
			},
		},
	})


	msgs = []
	lines = []
	player = players[ally_code]
	for unit in units:
		url = 'http://%s/swgoh/gear-levels/%s/' % (config['server'], unit.base_id)
		response, error = http_get(url)
		if error:
			raise Exception('101 %s' % error)

		if response.status_code != 200:
			raise Exception('Request failed to %s' % url)

		fields = []
		json = response.json()
		for name, data in json.items():
			unit_name = translate(unit.base_id, language)
			lines.append('**[%s](%s)**' % (unit_name, data['url']))
			min_gear_level = player['roster'][unit.base_id]['gear']
			for tier in reversed(range(min_gear_level, 13)):
				sublines = []
				tier_str = str(tier)
				for slot in sorted(data['tiers'][tier_str]):
					gear_id = data['tiers'][tier_str][slot]['gear']
					gear_url = data['tiers'][tier_str][slot]['url']
					gear_name = translate(gear_id, language)
					equipped = False
					for gear in player['roster'][unit.base_id]['equipped']:
						if tier == player['roster'][unit.base_id]['gear']:
							if int(slot) == gear['slot']:
								equipped = True
								break

					bold = not equipped and '**' or ''

					sublines.append('%sSlot%s: [%s](%s)%s' % (bold, (int(slot)+1), gear_name, gear_url, bold))

				gear_tier_id = 'Unit_Tier%02d' % tier
				gear_tier_title = translate(gear_tier_id, language)

				fields.append({
					'name': '== %s ==' % gear_tier_title,
					'value': '\n'.join(sublines),
				})

		msgs.append({
			#'title': '== Needed Gear ==',
			'description': '\n'.join(lines),
			'author': {
				'name': unit.name,
				'icon_url': get_avatar_url(unit.base_id),
			},
			'image': unit.get_image(),
			'fields': fields,
		})

	return msgs
