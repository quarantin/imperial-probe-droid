#!/usr/bin/python3

from opts import *
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

def cmd_gear(config, author, channel, args):

	args, units = parse_opts_unit_names(config, args)
	if args:
		plural = len(args) > 1 and 's' or ''
		return [{
			'title': 'Error: Unknown Parameter%s' % plural,
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
		}]

	if not units:
		return [{
			'title': 'Error: Missing Unit Name',
			'color': 'red',
			'description': 'I need at least one unit name.',
		}]

	msgs = []
	lines = []
	for unit in units:
		url = 'http://zeroday.biz/swgoh/gear-levels/%s/' % unit['base_id']
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
				lines.append('== Gear%d ==' % tier)
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
