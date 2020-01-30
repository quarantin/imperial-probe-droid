from opts import *
from errors import *
from swgohhelp import fetch_players, get_unit_name

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

def parse_opts_locked(request):

	opts = []
	args = request.args
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

	return opts
	
def cmd_locked(request):

	args = request.args
	config = request.config

	language = parse_opts_lang(request)

	players, error = parse_opts_players(request)

	opts = parse_opts_locked(request)

	if args:
		return error_unknown_parameters(args)

	if error:
		return error

	ally_codes = [ player.ally_code for player in players ]
	players = fetch_players(config, ally_codes)

	units = BaseUnit.objects.filter(combat_type=1).values()
	ships = BaseUnit.objects.filter(combat_type=2).values()
	char_list = { x['base_id']: x for x in units }
	ship_list = { x['base_id']: x for x in ships }

	msgs = []
	lines = []
	for ally_code, player in players.items():

		ally_units = player['roster']

		if opts in [ 'chars', 'all' ]:

			locked_chars = []
			for base_id, char in char_list.items():
				if base_id not in ally_units:
					char_name = get_unit_name(base_id, language)
					locked_chars.append(char_name)

			if not locked_chars:
				locked_chars.append('All characters unlocked!')

			lines.append('**Locked Characters**')
			lines += sorted(locked_chars)
			lines.append('')

		if opts in [ 'ships', 'all' ]:

			locked_ships = []
			for base_id, ship in ship_list.items():
				if base_id not in ally_units:
					ship_name = get_unit_name(base_id, language)
					locked_ships.append(ship_name)

			if not locked_ships:
				locked_ships.append('All ships unlocked!')

			lines.append('**Locked Ships**')
			lines += sorted(locked_ships)
			lines.append('')

		msgs.append({
			'author': {
				'name': '%s\'s Locked Units' % player['name'],
			},
			'title': '',
			'description': '\n'.join(lines),
		})

	return msgs
