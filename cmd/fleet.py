#!/usr/bin/python3

from opts import *
from swgoh import *

help_fleet = {
	'title': 'Player info',
	'description': """Shows fleet arena team for the supplied ally codes according to the supplied output format.

**Syntax**
```
%prefixfleet [ally codes or mentions] [output format]
%prefixfleet [ally codes or mentions] custom [format]```

**Aliases**
```
%prefixf```

**Output Formats**
See `!format` to list available formats, and `!help format` to see how to define new formats.

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
Also spaces need to be replaced with %20 and newlines with %0A.

**Examples**
```
%prefixf
%prefixf lite
%prefixf @Someone
%prefixf 123456789
%prefixf 123456789 234567891 verbose
%prefixf 123456788 lite
%prefixf custom %speed%20%name```"""
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

		if player:
			msgs.append({
				'title': 'Fleet Arena Team of %s (Rank: %s)\n%s' % (player, rank, profile_url),
				'description': '%s\n%s' % (config['separator'], '\n'.join(team)),
			})
		else:
			url = 'https://swgoh.gg/p/%s/' % ally_code
			msgs.append({
				'title': 'Not Found',
				'color': 'red',
				'description': 'Are you sure `%s` is a valid ally code and the account actually exists on swgoh.gg? Please check this URL to see: %s' % (ally_code, url)
			})

	return msgs
