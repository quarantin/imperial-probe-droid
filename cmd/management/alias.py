#!/usr/bin/python3

from errors import *

help_alias = {
	'title': 'Alias Help',
	'description': """Manages command aliases.

**Syntax**
```
%prefixalias
%prefixalias add [alias name] [command]
%prefixalias del [alias name or alias ID]```
**Aliases**
```
%prefixA```
**Examples**
List all alias defined:
```
%prefixA```
Add a new alias **`mm`** for **`%prefixmods missing`**:
```
%prefixA add mm mods missing```
Add a new alias **`myalias`** for **`%prefixarena custom "SPEED: %speed UNIT: %name"`**
```
%prefixA add myalias arena custom %speed%20%name```
Delete alias **`myalias`**:
```
%prefixA del myalias```
Delete first alias by its ID (**`mm`**):
```
%prefixA del 1```"""
}

def cmd_alias(config, author, channel, args):

	lines = []
	prefix = config['prefix']

	if not args:

		i = 1
		for alias, command in sorted(config['aliases'].items()):
			lines.append('**[%d]** **%s%s** `%s`' % (i, prefix, alias, command))
			i = i + 1

		return [{
			'title': 'Alias List',
			'description': '\n'.join(lines),
		}]

	action = args[0]

	if action == 'del':

		if len(args) < 2:
			return error_missing_parameter('alias')

		alias_name = args[1]
		if alias_name.isdigit():
			alias_name = int(alias_name)

			i = 1
			for alias, command in sorted(config['aliases'].items()):
				if i == alias_name:
					alias_name = alias
					del config['aliases'][alias_name]
					break

				i = i + 1
		elif alias_name in config['aliases']:
			del config['aliases'][alias_name]

		config['save']()
		return [{
			'title': 'Delete alias',
			'description': 'The alias `%s` was successfully deleted.' % alias_name,
		}]

	elif action == 'add':

		if len(args) < 3:
			return [{
				'title': 'Error: Missing Parameters',
				'color': 'red',
				'description': 'Please see !help alias.',
			}]

		alias_name = args[1]
		alias_command = ' '.join(args[2:])
		if alias_command.startswith(config['prefix']):
			alias_command = alias_command[1:]

		config['aliases'][alias_name] = alias_command

		config['save']()
		return [{
			'title': 'Add alias',
			'description': 'The alias `%s` was successfully added.' % alias_name,
		}]

	return [{
		'title': 'Error: Invalid Action',
		'color': 'red',
		'description': '`%s` is not a valid action. Please see `%shelp alias` for a list of valid actions.' % (action, config['prefix']),
	}]
