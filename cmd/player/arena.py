#!/usr/bin/python3

from datetime import datetime, timedelta

from opts import *
from errors import *
from utils import format_char_stats, format_char_details

from swgohhelp import fetch_crinolo_stats
from swgohgg import get_swgohgg_profile_url

help_arena = {
	'title': 'Arena Help',
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
	'char':  'chars',
	'chars': 'chars',
	's':     'ships',
	'ship':  'ships',
	'ships': 'ships',
	'f':     'ships',
	'fleet': 'ships',
}

def parse_opts_arena(args):

	selected_opts = 'chars'
	args_cpy = list(args)

	for arg in args_cpy:

		if arg in opts_arena:
			args.remove(arg)
			opt = opts_arena[arg]
			return args, opt

	return args, selected_opts

def cmd_arena(config, author, channel, args):

	args, selected_opts = parse_opts_arena(args)
	if not selected_opts:
		selected_opts.append('chars')

	args, selected_players, error = parse_opts_players(config, author, args)

	args, selected_format = parse_opts_format(config, selected_opts, args)

	if args:
		return error_unknown_parameters(args)

	if error:
		return error

	ally_codes = [ int(player.ally_code) for player in selected_players ]
	stats, players = fetch_crinolo_stats(config, ally_codes)
	players = { player['allyCode']: player for player in players }

	msgs = []
	for ally_code in ally_codes:

		utc_offset = players[ally_code]['poUTCOffsetMinutes']
		last_sync_date = datetime.fromtimestamp(int(players[ally_code]['updated']) / 1000) + timedelta(minutes=utc_offset)
		last_sync = last_sync_date.strftime('%Y-%m-%d at %H:%M:%S')
		profile_url = get_swgohgg_profile_url(ally_code)

		player = players[ally_code]['name']
		if not player:
			msgs.extend(error_ally_code_not_found(ally_code))
			continue

		if 'chars' == selected_opts:
			rank = players[ally_code]['arena']['char']['rank']
			squad = players[ally_code]['arena']['char']['squad']
			lines = []
			for squad_unit in squad:
				base_id = squad_unit['defId']
				roster = { unit['defId']: unit for unit in players[ally_code]['roster'] }
				unit = roster[base_id]
				unit['squadUnitType'] = squad_unit['squadUnitType']
				line = format_char_details(unit, selected_format)
				line = format_char_stats(stats[ally_code][base_id], line)
				lines.append(line)

			msgs.append({
				'title': 'Arena Squad of %s (Rank: %s)\n%s' % (player, rank, profile_url),
				'description': 'Last Sync: %s\n%s\n%s' % (last_sync, config['separator'], ('\n'.join(lines)).strip()),
			})

		if 'ships' == selected_opts:
			rank = players[ally_code]['arena']['ship']['rank']
			squad = players[ally_code]['arena']['ship']['squad']
			lines = []
			for squad_unit in squad:
				base_id = squad_unit['defId']
				roster = { unit['defId']: unit for unit in players[ally_code]['roster'] }
				unit = roster[base_id]
				unit['squadUnitType'] = squad_unit['squadUnitType']
				line = format_char_details(unit, selected_format)
				#line = format_char_stats(stats[ally_code][base_id], line)
				lines.append(line)

			msgs.append({
				'title': 'Fleet Arena Squad of %s (Rank: %s)\n%s' % (player, rank, profile_url),
				'description': 'Last Sync: %s\n%s\n%s' % (last_sync, config['separator'], ('\n'.join(lines)).strip()),
			})

	return msgs
