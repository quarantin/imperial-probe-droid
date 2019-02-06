#!/usr/bin/python3

from opts import *
from swgoh import *

help_fleet = {
	'title': 'Player info',
	'description': """Shows fleet arena team for the supplied ally codes according to the supplied output format.

**Syntax**
```
%prefixfleet [ally codes or mentions] [output format]
%prefixfleet [ally codes or mentions] custom "format"```
**Aliases**
```
%prefixf```
**Output Formats**
See **`!format`** to list available formats, and **`!help format`** to see how to define new formats.

**Custom Format**
The custom format can contain the following keywords:
```
%name (character name)
%leader (leader of the group)
%level (level of the character)
%gear (level of gear of the character)
%power (power of the character)
%health (health of the character)
%speed (speed of the character)
...```
**Examples**
Show your fleet arena team:
```
%prefixf```
Show your fleet arena team using the output format **`lite`**:
```
%prefixf lite```
Show fleet arena team of someone by mention:
```
%prefixf @Someone```
Show fleet arena team of someone by discord nick (no hilight):
```
%prefixf "Someone"```
Show fleet arena team of someone by ally code:
```
%prefixf 123456789```
Show fleet arena team of two players using the output format **`verbose`**
```
%prefixf 123456789 234567891 verbose```
Show your fleet arena team using a custom format:
```
%prefixf custom "SPEED: %speed UNIT: %name%leader"```"""
}

def cmd_fleet(config, author, channel, args):

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
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(new_args)),
		}]

	msgs = []
	for ally_code in ally_codes:

		player = get_player_name(ally_code)
		rank = get_fleet_rank(ally_code)
		profile_url = get_swgoh_profile_url(ally_code)
		team = get_fleet_team(ally_code, selected_format)
		last_sync = get_last_sync(ally_code)

		if player:
			msgs.append({
				'title': 'Fleet Arena Team of %s (Rank: %s)\n%s' % (player, rank, profile_url),
				'description': 'Last Sync: %s\n%s\n%s' % (last_sync, config['separator'], ('\n'.join(team)).strip()),
			})
		else:
			url = 'https://swgoh.gg/p/%s/' % ally_code
			msgs.append({
				'title': 'Not Found',
				'color': 'red',
				'description': 'Are you sure `%s` is a valid ally code and the account actually exists on swgoh.gg? Please check this URL to see: %s' % (ally_code, url)
			})

	return msgs
