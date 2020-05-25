from datetime import datetime, timedelta

from opts import *
from utils import format_char_stats, format_char_details

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

def parse_opts_arena(ctx):

	selected_opts = 'chars'
	args = ctx.args
	args_cpy = list(args)

	for arg in args_cpy:

		if arg in opts_arena:
			args.remove(arg)
			opt = opts_arena[arg]
			return opt

	return selected_opts

async def cmd_arena(ctx):

	bot = ctx.bot
	args = ctx.args
	config = ctx.config

	selected_opts = parse_opts_arena(ctx)
	if not selected_opts:
		selected_opts.append('chars')

	selected_players, error = parse_opts_players(ctx)

	selected_format = parse_opts_format(ctx, selected_opts)

	if error:
		return error

	if args:
		return bot.errors.unknown_parameters(args)

	if not selected_players:
		return bot.errors.no_ally_code_specified(ctx)

	ally_codes = [ x.ally_code for x in selected_players ]
	players = await bot.client.players(ally_codes=ally_codes, stats=True)
	if not players:
		return bot.errors.ally_codes_not_found(ally_codes)

	players = { x['allyCode']: x for x in players }

	msgs = []
	for player in selected_players:

		ally_code = player.ally_code
		jplayer = players[ally_code]
		jroster = { x['defId']: x for x in jplayer['roster'] }

		last_sync_date = datetime.fromtimestamp(int(jplayer['updated']) / 1000) #+ timedelta(minutes=utc_offset)
		last_sync = last_sync_date.strftime('%Y-%m-%d at %H:%M:%S')
		profile_url = await get_swgohgg_profile_url(jplayer['allyCode'])
		if not profile_url:
			profile_url = 'No profile found on swgoh.gg for ally code: %s' % ally_code_str

		if 'chars' == selected_opts:
			rank = jplayer['arena']['char']['rank']
			squad = jplayer['arena']['char']['squad']
			lines = []
			for squad_unit in squad:
				base_id = squad_unit['defId'].split(':', 1)[0]
				unit = jroster[base_id]
				unit['role'] = squad_unit['role']
				line = format_char_details(unit, selected_format)
				line = format_char_stats(unit, line)
				lines.append(line)

			msgs.append({
				'title': 'Arena Squad of %s (Rank: %s)\n%s' % (jplayer['name'], rank, profile_url),
				'description': 'Last Sync: %s\n%s\n%s' % (last_sync, config['separator'], ('\n'.join(lines)).strip()),
			})

		if 'ships' == selected_opts:
			rank = jplayer['arena']['ship']['rank']
			squad = jplayer['arena']['ship']['squad']
			lines = []
			for squad_unit in squad:
				base_id = squad_unit['defId'].split(':', 1)[0]
				unit = jroster[base_id]
				unit['role'] = squad_unit['role']
				line = format_char_details(unit, selected_format)
				line = format_char_stats(unit, line)
				lines.append(line)

			msgs.append({
				'title': 'Fleet Arena Squad of %s (Rank: %s)\n%s' % (jplayer['name'], rank, profile_url),
				'description': 'Last Sync: %s\n%s\n%s' % (last_sync, config['separator'], ('\n'.join(lines)).strip()),
			})

	return msgs
