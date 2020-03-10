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

def parse_opts_arena(request):

	selected_opts = 'chars'
	args = request.args
	args_cpy = list(args)

	for arg in args_cpy:

		if arg in opts_arena:
			args.remove(arg)
			opt = opts_arena[arg]
			return opt

	return selected_opts

async def cmd_arena(request):

	args = request.args
	config = request.config

	selected_opts = parse_opts_arena(request)
	if not selected_opts:
		selected_opts.append('chars')

	selected_players, error = parse_opts_players(request)

	selected_format = parse_opts_format(request, selected_opts)

	if args:
		return error_unknown_parameters(args)

	if error:
		return error

	ally_codes = [ player.ally_code for player in selected_players ]
	stats, players = await fetch_crinolo_stats(config, ally_codes)
	players = { str(player['allyCode']): player for player in players }

	msgs = []
	for ally_code_str, player in players.items():

		ally_code = int(ally_code_str)
		#utc_offset = player['poUTCOffsetMinutes']
		last_sync_date = datetime.fromtimestamp(int(player['updated']) / 1000) #+ timedelta(minutes=utc_offset)
		last_sync = last_sync_date.strftime('%Y-%m-%d at %H:%M:%S')
		profile_url = await get_swgohgg_profile_url(player['allyCode'])
		if not profile_url:
			profile_url = 'No profile found on swgoh.gg for ally code: %s' % ally_code_str

		if 'chars' == selected_opts:
			rank = player['arena']['char']['rank']
			squad = player['arena']['char']['squad']
			lines = []
			for squad_unit in squad:
				base_id = squad_unit['defId'].split(':', 1)[0]
				unit = stats[ally_code][base_id]
				unit['squadUnitType'] = squad_unit['squadUnitType']
				line = format_char_details(unit, selected_format)
				line = format_char_stats(stats[ally_code][base_id], line)
				lines.append(line)

			msgs.append({
				'title': 'Arena Squad of %s (Rank: %s)\n%s' % (player['name'], rank, profile_url),
				'description': 'Last Sync: %s\n%s\n%s' % (last_sync, config['separator'], ('\n'.join(lines)).strip()),
			})

		if 'ships' == selected_opts:
			rank = player['arena']['ship']['rank']
			squad = player['arena']['ship']['squad']
			lines = []
			for squad_unit in squad:
				base_id = squad_unit['defId'].split(':', 1)[0]
				unit = stats[ally_code][base_id]
				unit['squadUnitType'] = squad_unit['squadUnitType']
				line = format_char_details(unit, selected_format)
				line = format_char_stats(stats[ally_code][base_id], line)
				lines.append(line)

			msgs.append({
				'title': 'Fleet Arena Squad of %s (Rank: %s)\n%s' % (player['name'], rank, profile_url),
				'description': 'Last Sync: %s\n%s\n%s' % (last_sync, config['separator'], ('\n'.join(lines)).strip()),
			})

	return msgs
