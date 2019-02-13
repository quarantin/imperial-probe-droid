#!/usr/bin/python3

from opts import *
from utils import format_char_stats, format_char_details

from swgohhelp import fetch_players, fetch_units, get_player_name, get_last_sync, get_arena_rank, get_arena_squad, get_stats
from swgohgg import get_swgohgg_profile_url

help_arena = {
	'title': 'Player info',
	'description': """Shows arena squads for the supplied players according to the supplied output format.

**Syntax**
```
%prefixarena [players] [options] [format name]
%prefixarena [players] [options] custom [custom format]```
**Aliases**
**`%prefixa`**: Direct alias for **`%prefixarena`**.
**`%prefixac`**: Alias for arena squad only (%prefixarena chars).
**`%prefixaf`**: Alias for fleet arena squad only (%prefixarena ships).

**Options**
Valid options can be:
**`chars`** (or **`c`**): To show arena squad.
**`fleet`** (or **`f`**): To show fleet arena squad.
**`ships`** (or **`s`**): An alias for **`fleet`**
Display both arena and fleet arena squads by default.

**Output Formats**
See **`!format`** to list available formats, and **`!help format`** to learn how to define new formats.

**Custom Format**
The custom format can contain the following keywords:
```
%name (character name)
%role (role in the group)
%level (level of the character)
%gear (level of gear of the character)
%gp (galactic power of the character)
%health (health of the character)
%speed (speed of the character)
%critical-damage
%physical-critical-chance
%special-critical-chance
%physical-critical-avoidance
%special-critical-avoidance
%physical-accuracy
TODO (ping me on discord about it)
...```
**Examples**
Showing both your arena and fleet arena squads:
```
%prefixa```
Showing only your fleet arena squad using the output format **`lite`**:
```
%prefixa ships lite```
Showing arena squad of someone by mention using default output format:
```
%prefixa chars @Someone```
Showing arena squad of someone by discord nick (no hilight):
```
%prefixa 123456789```
Showing only your arena squad using a custom format:
```
%prefixa chars custom "SPEED: %speed UNIT: %name%leader"```"""
}

opts_arena = {
	'c':     'chars',
	'chars': 'chars',
	'f':     'ships',
	'fleet': 'ships',
	's':     'ships',
	'ships': 'ships',
}

def parse_opts_arena(args):

	selected_opts = []
	args_cpy = list(args)

	for arg in args_cpy:

		if arg in opts_arena:
			args.remove(arg)
			opt = opts_arena[arg]
			if opt not in selected_opts:
				selected_opts.append(opt)

	return args, selected_opts

def cmd_arena(config, author, channel, args):

	args, selected_opts = parse_opts_arena(args)
	if not selected_opts:
		selected_opts.extend([ 'chars' ])

	args, ally_codes = parse_opts_ally_codes(config, author, args)
	if not ally_codes:
		return [{
			'title': 'Not Found',
			'color': 'red',
			'description': 'No ally code specified, or found registered to <%s>' % author,
		}]

	args, selected_format = parse_opts_format(config, args)
	if args:
		plural = len(args) > 1 and 's' or ''
		return [{
			'title': 'Unknown Parameter%s' % plural,
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
		}]

	players = fetch_players(config, ally_codes)
	units = fetch_units(config, ally_codes)

	msgs = []
	for ally_code in ally_codes:

		player = get_player_name(config, ally_code)
		last_sync = get_last_sync(config, ally_code, '%Y-%m-%d at %H:%M:%S')
		profile_url = get_swgohgg_profile_url(ally_code)

		if not player:
			url = 'https://swgoh.gg/p/%s/' % ally_code
			msgs.append({
				'title': 'Not Found',
				'color': 'red',
				'description': 'Are you sure `%s` is a valid ally code and the account actually exists on swgoh.gg? Please check this URL to see: %s' % (ally_code, url)
			})
			continue

		if 'chars' in selected_opts:
			rank = get_arena_rank(config, ally_code, 'char')
			squad = get_arena_squad(config, ally_code, 'char')
			lines = []
			for squad_unit in squad:
				base_id = squad_unit['defId']
				unit = players[int(ally_code)]['roster-by-id'][base_id]
				unit['squadUnitType'] = squad_unit['squadUnitType']
				stats = get_stats(config, ally_code)
				line = format_char_details(unit, selected_format)
				line = format_char_stats(stats[base_id], line)
				lines.append(line)

			msgs.append({
				'title': 'Arena Squad of %s (Rank: %s)\n%s' % (player, rank, profile_url),
				'description': 'Last Sync: %s\n%s\n%s' % (last_sync, config['separator'], ('\n'.join(lines)).strip()),
			})

		if 'ships' in selected_opts:
			rank = get_arena_rank(config, ally_code, 'ship')
			squad = get_arena_squad(config, ally_code, 'ship') #, selected_format)
			lines = []
			for squad_unit in squad:
				base_id = squad_unit['defId']
				unit = players[int(ally_code)]['roster-by-id'][base_id]
				unit['squadUnitType'] = squad_unit['squadUnitType']
				stats = { base_id: {} }
				# No stats for ships yet (See with Crinolo)
				# stats = get_stats(config, ally_code)
				line = format_char_details(unit, selected_format)
				line = format_char_stats(stats[base_id], line)
				lines.append(line)

			msgs.append({
				'title': 'Fleet Arena Squad of %s (Rank: %s)\n%s' % (player, rank, profile_url),
				'description': 'Last Sync: %s\n%s\n%s' % (last_sync, config['separator'], ('\n'.join(lines)).strip()),
			})

	return msgs
