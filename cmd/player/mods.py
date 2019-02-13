#!/usr/bin/python3

from opts import *
from swgoh import *

help_mods = {
	'title': 'Player info',
	'description': """Shows statistics about mods for the supplied ally codes.

**Syntax**
```
%prefixmods [ally_codes or mentions] [option]```

**Options**
```
missing (or m): To show units with missing mods.
nomods (or n): To show units with no mods.
incomplete (or i): To show units with incomplete modsets.```

**Aliases**
```
%prefixm```

**Examples**
```
%prefixm
%prefixm @Someone
%prefixm 123456789
%prefixm 123456789 missing
%prefixm nomods
%prefixm incomplete```""",
}

def cmd_mods(config, author, channel, args):

	args, ally_codes = parse_opts_ally_codes(config, author, args)
	if not ally_codes:
		return

	action = ''
	for arg in args:

		if arg in [ 'm', 'missing' ]:
			action = 'missing'

		elif arg in [ 'n', 'nomods' ]:
			action = 'nomods'

		elif arg in [ 'i', 'incomplete' ]:
			action = 'incomplete'

	msgs = []
	units_with_missing_mods = []
	units_with_incomplete_modsets = []

	for ally_code in ally_codes:

		player = get_player_name(ally_code)

		if not action:
			msgs.append({
				'title': '%s\'s Mods' % player,
				'description': '%s has %d equipped mods.' % (player, get_mods_count(ally_code)),
			})

		elif action == 'missing':
			lines = []
			units = get_units_with_missing_mods(ally_code)
			for unit in units:
				lines.append(' - %d mods missing for %s' % (len(unit['missing-mods']), unit['name']))

			msgs.append({
				'title': 'Units with missing mods for %s' % player,
				'description': '\n'.join(reversed(sorted(lines))),
			})

		elif action == 'nomods':
			lines = []
			units = get_units_with_no_mods(ally_code)
			for unit in units:
				lines.append(' - %s' % unit['name'])

			msgs.append({
				'title': 'Units with no mods for %s' % player,
				'description': '\n'.join(sorted(lines))
			})
		elif action == 'incomplete':
			lines = []
			units = get_units_with_incomplete_modsets(ally_code)
			for unit in units:
				lines.append(' - %s' % unit['name'])

			msgs.append({
				'title': 'Units with incomplete modsets for %s' % player,
				'description': '\n'.join(sorted(lines)),
			})

		else:
			return [{
				'title': 'Unknown Parameters',
				'description': 'I don\'t know what to do with the following parameters:\n - %s' % '\n - '.join(args),
			}]

	return msgs
