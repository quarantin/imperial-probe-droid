#!/usr/bin/python3

from opts import *

help_nicks = {
	'title': 'Nicks Help',
	'description': """Handles the list of nicknames (list/add/delete) for units and ships.

**Syntax**
```
%prefixnicks
%prefixnicks add [nick] [unit or ship]
%prefixnicks del [nick or nick ID]```

**Aliases**
```
%prefixN```

**Examples**
```
%prefixN
%prefixN add ep palpatine
%prefixN add gat thrawn
%prefixN del gat
%prefixN del 1```"""
}

def cmd_nicks(config, author, channel, args):

	lines = []
	prefix = config['prefix']

	if not args:

		i = 1
		for nick, name in sorted(config['nicks'].items()):
			lines.append('**[%d]** **%s** `%s`' % (i, nick, name))
			i = i + 1

		return [{
			'title': 'Character Nick List',
			'description': '\n'.join(lines),
		}]

	action = args.pop(0)

	if action == 'del':

		if len(args) < 1:
			return [{
				'title': 'Missing Parameters',
				'color': 'red',
				'description': 'Please see !help nicks.',
			}]

		target_nick = args.pop(0)
		if target_nick.isdigit():
			target_nick = int(target_nick)

			i = 1
			for nick, name in sorted(config['nicks'].items()):
				if i == target_nick:
					del config['nicks'][nick]
					break

				i = i + 1
		elif target_nick in config['nicks']:
			del config['nicks'][target_nick]

		config['save']()
		return [{
			'title': 'Delete Nick',
			'description': 'The nickname was successfully deleted.',
		}]

	elif action == 'add':

		if len(args) < 2:
			return [{
				'title': 'Missing Parameters',
				'color': 'red',
				'description': 'Please see !help nicks.',
			}]

		target_nick = args.pop(0)
		args, selected_units = parse_opts_unit_names(config, args)
		if args:
			plural = len(args) > 1 and 's' or ''
			return [{
				'title': 'Unknown Parameter%s' % plural, 
				'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
			}]

		if not selected_units:
			return [{
				'title': 'No Unit Selected',
				'description': 'You need to provide at least one unit or ship name',
			}]

		if len(selected_units) > 1:
			return [{
				'title': 'Invalid Number of Units',
				'description': 'You provided %d units but you have to supply only one.' % len(selected_units)
			}]

		config['nicks'][target_nick] = selected_units.pop(0)['name']

		config['save']()
		return [{
			'title': 'Add Nick',
			'description': 'The nickname was successfully added.',
		}]

	return [{
		'title': 'TODO',
		'description': 'TODO',
	}]
