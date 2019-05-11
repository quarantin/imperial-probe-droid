#!/usr/bin/python3

from opts import *
from errors import *
from utils import http_get

from swgohgg import get_avatar_url

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

roman_numbers = {
	1: 'I',
	2: 'II',
	3: 'III',
	4: 'IV',
	5: 'V',
	6: 'VI',
	7: 'VII',
	8: 'VIII',
	9: 'IX',
	10: 'X',
	11: 'XI',
	12: 'XII',
}

def cmd_gear(config, author, channel, args):

	args, players, error = parse_opts_players(config, author, args, min_allies=1, max_allies=1)

	args, units = parse_opts_unit_names(config, args)

	if args:
		return error_unknown_parameters(args)

	if not units:
		return error_no_unit_selected()

	if not players:
		return error

	player = players[0]

	msgs = []
	lines = []
	for unit in units:
		url = 'http://%s/swgoh/gear-levels/%s/%s/' % (config['server'], unit['base_id'], player.ally_code)
		response, error = http_get(url)
		if error:
			raise Exception('101 %s' % error)

		if response.status_code != 200:
			raise Exception('Request failed to %s' % url)

		json = response.json()
		for name, data in json.items():
			lines.append('[%s](%s)' % (name, data['url']))
			for tier in reversed(range(1, 13)):
				tier_str = str(tier)
				tier_data = data['tiers'][tier_str]
				lines.append('== Gear Lvl %s ==' % roman_numbers[tier])
				for slot in sorted(data['tiers'][tier_str]):
					gear_name = data['tiers'][tier_str][slot]['gear']
					gear_url = data['tiers'][tier_str][slot]['url']
					lines.append('\t - Slot%s: [%s](%s)' % ((int(slot)+1), gear_name, gear_url))
				lines.append('')
		msgs.append({
			'title': '== Needed Gear ==',
			'description': '\n'.join(lines),
			'author': {
				'name': unit['name'],
				'icon_url': get_avatar_url(unit['base_id']),
			},
			'image': unit['image'],
		})

	return msgs
