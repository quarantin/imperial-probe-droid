#!/usr/bin/python3

from opts import *
from swgoh import *

help_locked = {
	'title': 'Player info',
	'description': """Shows units and ships that are still locked for the supplied ally codes.

**Syntax**
```
%prefixlocked [ally codes]
%prefixlocked [ally codes] [options]```

**Aliases**
```
%prefixl```

**Options**
```
units (or u)
ships (or s)```

**Examples**
```
%prefixl
%prefixl u
%prefixl ships
%prefixl 123456789 units
%prefixl 123456789 234567891```"""
}

def parse_opts_units_or_ships(args):

	opts = 'all'
	args_cpy = list(args)

	for arg in args_cpy:

		if arg in [ 'u', 'units' ]:
			opts = 'units'
			args.remove(arg)

		elif arg in [ 's', 'ships' ]:
			opts = 'ships'
			args.remove(arg)

	return args, opts
	
def cmd_locked(config, author, channel, args):

	args, ally_codes = parse_opts_ally_codes(config, author, args)
	if not ally_codes:
		return [{
			'title': 'Not Found',
			'color': 'red',
			'description': 'No ally code specified, or found registered to <%s>' % author,
		}]

	args, opts = parse_opts_units_or_ships(args)
	if args:
		plural = len(args) > 1 and 's' or ''
		return [{
			'title': 'Unknown Parameter%s' % plural,
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
		}]

	all_units = get_all_units()
	all_ships = get_all_ships()

	msgs = []
	for ally_code in ally_codes:

		player = get_player_name(ally_code)
		if not player:
			url = 'https://swgoh.gg/p/%s/' % ally_code
			msgs.append({
				'title': 'Not Found',
				'color': 'red',
				'description': 'Are you sure `%s` is a valid ally code and the account actually exists on swgoh.gg? Please check this URL to see: %s' % (ally_code, url)
			})
			continue

		ally_db = get_my_units_and_ships(ally_code)

		if opts in [ 'units', 'all' ]:

			locked_units = []
			for base_id, unit in all_units.items():
				if base_id not in ally_db['units']:
					locked_units.append(unit['name'])

			if not locked_units:
				locked_units.append('All units unlocked!')

			msgs.append({
				'title': 'Locked units for %s' % player,
				'description': '%s\n%s' % (config['separator'], '\n'.join(locked_units)),
				})

		if opts in [ 'ships', 'all' ]:

			locked_ships = []
			for base_id, ship in all_ships.items():
				if base_id not in ally_db['ships']:
					locked_ships.append(ship['name'])

			if not locked_ships:
				locked_ships.append('All ships unlocked!')

			msgs.append({
				'title': 'Locked ships for %s' % player,
				'description': '%s\n%s' % (config['separator'], '\n'.join(locked_ships)),
				})

	return msgs
