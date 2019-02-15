#!/usr/bin/python3

from opts import *
from swgohgg import get_char_list, get_ship_list
from swgohhelp import fetch_players, fetch_units, get_player_name

help_locked = {
	'title': 'Locked Help',
	'description': """Shows characters and ships that are still locked for the supplied players.

**Syntax**
```
%prefixlocked [players] [options]```
**Aliases**
```
%prefixl```

**Options**
The following options are available to filter output:
**`chars`** (or **`c`**): To show locked characters for the specified players.
**`ships`** (or **`s`**): To show locked ships for the specificed players.
If no options are specified, all locked characters and ships are displayed.
**Examples**
Show your locked characters and ships:
```
%prefixl```
Show only your locked characters:
```
%prefixl c```
Show only your locked ships:
```
%prefixl ships```
Show locked characters and ships for someone by mention:
```
%prefixl @Someone```
Show locked characters and ships for someone by discord-nick (no hilight):
```
%prefixl "Someone"```
Show locked characters for someone by ally code:
```
%prefixl 123456789 chars```
Show locked characters and ships for two different ally codes:
```
%prefixl 123456789 234567891```"""
}

opts_locked = {
	'c':     'chars',
	'chars': 'chars',
	's':     'ships',
	'ships': 'ships',
}

def parse_opts_locked(args):

	opts = []
	args_cpy = list(args)

	for arg in args_cpy:

		if arg in opts_locked:
			args.remove(arg)
			opt = opts_locked[arg]
			if opt not in opts:
				opts.append(opt)

	if not opts or len(opts) >= 2:
		opts = 'all'
	else:
		opts = opts.pop(0)

	return args, opts
	
def cmd_locked(config, author, channel, args):

	args, ally_codes = parse_opts_ally_codes(config, author, args)
	if not ally_codes:
		return [{
			'title': 'Not Found',
			'color': 'red',
			'description': 'No ally code specified or found registered to <%s>' % author,
		}]

	args, opts = parse_opts_locked(args)
	if args:
		plural = len(args) > 1 and 's' or ''
		return [{
			'title': 'Unknown Parameter%s' % plural,
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
		}]

	all_ships = get_ship_list()

	players = fetch_players(config, ally_codes)
	units = fetch_units(config, ally_codes)

	msgs = []
	for ally_code in ally_codes:

		ally_code = int(ally_code)
		ally_units = units[ally_code]

		player = get_player_name(config, ally_code)
		if not player:
			url = 'https://swgoh.gg/p/%s/' % ally_code
			msgs.append({
				'title': 'Not Found',
				'color': 'red',
				'description': 'Are you sure `%s` is a valid ally code and the account actually exists on swgoh.gg? Please visit this URL to check: %s' % (ally_code, url)
			})
			continue

		if opts in [ 'chars', 'all' ]:

			locked_chars = []
			for char in get_char_list():
				base_id = char['base_id']
				if base_id not in ally_units:
					locked_chars.append(char['name'])

			if not locked_chars:
				locked_chars.append('All units unlocked!')

			msgs.append({
				'title': 'Locked Characters',
				'author': {
					'name': '%s' % player,
				},
				'description': '%s\n%s' % (config['separator'], '\n'.join(locked_chars)),
				})

		if opts in [ 'ships', 'all' ]:

			locked_ships = []
			for ship in all_ships:
				base_id = ship['base_id']
				if base_id not in ally_units:
					locked_ships.append(ship['name'])

			if not locked_ships:
				locked_ships.append('All ships unlocked!')

			msgs.append({
				'title': 'Locked Ships',
				'author': {
					'name': '%s' % player,
				},
				'description': '%s\n%s' % (config['separator'], '\n'.join(locked_ships)),
				})

	return msgs
