#!/usr/bin/python3

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
```
%prefixalias
%prefixalias add mm mods missing
%prefixalias add myalias arena custom %speed%20%name
%prefixalias del myalias
%prefixalias del 1```"""
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
			return [{
				'title': 'Missing Parameters',
				'color': 'red',
				'description': 'Please see !help alias.',
			}]

		alias_name = args[1]
		if alias_name.isdigit():
			alias_name = int(alias_name)

			i = 1
			for alias, command in sorted(config['aliases'].items()):
				if i == alias_name:
					del config['aliases'][alias]
					break

				i = i + 1
		elif alias_name in config['aliases']:
			del config['aliases'][alias_name]

		save_config(config)
		return [{
			'title': 'Delete alias',
			'description': 'The alias was successfully deleted.',
		}]

	elif action == 'add':

		if len(args) < 3:
			return [{
				'title': 'Missing Parameters',
				'color': 'red',
				'description': 'Please see !help alias.',
			}]

		alias_name = args[1]
		alias_command = ' '.join(args[2:])
		if alias_command.startswith(config['prefix']):
			alias_command = alias_command[1:]

		config['aliases'][alias_name] = alias_command

		save_config()
		return [{
			'title': 'Add alias',
			'description': 'The alias was successfully added.',
		}]

	return [{
		'title': 'TODO',
		'description': 'TODO',
	}]
