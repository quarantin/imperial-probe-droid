#!/usr/bin/python3

help_format = {
	'title': 'Format Help',
	'description': """Manages output formats.

**Syntax**
```
%prefixformat
%prefixformat add [format name] [format]
%prefixformat del [format name or format ID]```

**Aliases**
```
%prefixF```

**Examples**
```
%prefixF
%prefixF add fmt-info "%name%leader"
%prefixF add fmt-short "SPD:%speed%20HP:%health%20PR:%protection%20%name"
%prefixF del fmt-short
%prefixF del 1```"""
}

def cmd_format(config, author, channel, args):

	lines = []
	prefix = config['prefix']

	if not args:

		i = 1
		for fmt, command in sorted(config['formats'].items()):
			lines.append('**[%d]** **%s** `%s`' % (i, fmt, command))
			i = i + 1

		description = 'No formats available.'
		if lines:
			description = '\n'.join(lines)

		return [{
			'title': 'Format List',
			'description': description,
		}]

	action = args[0]

	if action == 'del':

		if len(args) < 2:
			return [{
				'title': 'Missing Parameters',
				'color': 'red',
				'description': 'Please see !help format.',
			}]

		success = False
		format_name = args[1]
		if format_name.isdigit():
			format_name = int(format_name)

			i = 1
			for fmt, command in sorted(config['formats'].items()):
				if i == format_name:
					del config['formats'][fmt]
					success = True
					break

				i = i + 1
		elif format_name in config['formats']:
			del config['formats'][format_name]
			success = True

		if success:
			config['save'](config)
			return [{
				'title': 'Delete Format',
				'description': 'The format was successfully deleted.',
			}]
		else:
			return [{
				'title': 'Delete Format',
				'color': 'red',
				'description': 'Could not find a format to delete with this index or name: `%s`.' % format_name,
			}]

	elif action == 'add':

		if len(args) < 3:
			return [{
				'title': 'Add Format',
				'color': 'red',
				'description': 'Missing parameters. Please see !help format.',
			}]

		format_name = args[1]
		custom_format = ' '.join(args[2:])
		if custom_format.startswith(config['prefix']):
			custom_format = custom_format[1:]

		config['formats'][format_name] = custom_format

		config['save'](config)
		return [{
			'title': 'Add Format',
			'description': 'The format was successfully added.',
		}]

	return [{
		'title': 'TODO',
		'description': 'TODO',
	}]
