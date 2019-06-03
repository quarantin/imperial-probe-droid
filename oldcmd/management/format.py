from errors import *

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
Show all output format defined:
```
%prefixF```
Add new output format **`fmt-info`** for **`%name%leader`**
```
%prefixF add fmt-info "%name%leader"```
Add new output format **`fmt-short`** for **`"SPD:%speed%20HP:%health%20PR:%protection%20%name"`**
```
%prefixF add fmt-short "SPD:%speed%20HP:%health%20PR:%protection%20%name"```
Delete output format **`fmt-short`**
```
%prefixF del fmt-short```
Delete first output format by its ID (**`fmt-info`**):
```
%prefixF del 1```"""
}

def cmd_format(config, author, channel, args):

	lines = []
	prefix = config['prefix']

	if not args:

		i = 1
		for fmt, command in sorted(config['formats'].items()):
			lines.append('**[%d]** **%s** "%s"' % (i, fmt, command))
			lines.append('')
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
			return error_missing_parameter('format')

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
			config['save']()
			return [{
				'title': 'Delete Format',
				'description': 'The format `%s` was successfully deleted.' % format_name,
			}]
		else:
			return [{
				'title': 'Error: Invalid Parameter',
				'color': 'red',
				'description': 'Could not find a format to delete with this index or name: `%s`.' % format_name,
			}]

	elif action == 'add':

		if len(args) < 3:
			return error_missing_parameter('format')

		format_name = args[1]
		custom_format = ' '.join(args[2:])
		if custom_format.startswith(config['prefix']):
			custom_format = custom_format[1:]

		config['formats'][format_name] = custom_format

		config['save']()
		return [{
			'title': 'Add Format',
			'description': 'The format `%s` was successfully added.' % format_name,
		}]

	return [{
		'title': 'Error: Invalid Action',
		'color': 'red',
		'description': '`%s` is not a valid action. Please see `%shelp format` for a list of valid actions.' % (action, config['prefix']),
	}]
