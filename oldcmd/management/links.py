from errors import *

help_links = {
	'title': 'Links Help',
	'description': """Manages URLs.

**Syntax**
```
%prefixlinks
%prefixlinks add [link name] [URL]
%prefixlinks del [link name or link ID]```
**Aliases**
```
%prefixL```
**Examples**
List all saved URLs:
```
%prefixL```
Add a new URL named `events`:
```
%prefixL add events https://swgohevents.com/```
Delete the URL named `events`:
```
%prefixL del events```"""
}

def cmd_links(config, author, channel, args):

	lines = []
	prefix = config['prefix']

	if not args:

		i = 1
		lines = []
		if 'links' in config:
			for name, link in sorted(config['links'].items()):
				lines.append('**[%d]** **%s** %s' % (i, name, link))
				i = i + 1

		if not lines:
			lines.append('No URL saved yet.')

		return [{
			'title': 'URL List',
			'description': '\n'.join(lines),
		}]

	action = args[0]

	if action == 'del':

		if len(args) < 2:
			return error_missing_parameter(config, 'links')

		found = False
		link_val = None
		link_name = args[1]
		if link_name.isdigit():

			i = 1
			for name, link in sorted(config['links'].items()):
				if i == int(link_name):
					link_name = name
					link_val = config['links'][name]
					del config['links'][name]
					found = True
					break

				i = i + 1

		elif link_name in config['links']:
			link_val = config['links'][link_name]
			del config['links'][link_name]
			found = True

		if found:
			if link_val in config['short-links']:
				del config['short-links'][link_val]

			config['save']()
			return [{
				'title': 'Delete URL',
				'description': 'The URL was successfully deleted:\n`%s`: %s' % (link_name, link_val),
			}]

		else:
			return [{
				'title': 'Error: Invalid Parameter',
				'color': 'red',
				'description': 'I could not find a link with name or ID `%d`. Please see `%shelp links` for a list of valid names and IDs.' % (link_name, config['prefix']),
			}]

	elif action == 'add':

		if len(args) < 3:
			return error_missing_parameter(config, 'links')

		link_name = args[1]
		link_val = args[2]

		if 'links' not in config:
			config['links'] = {}

		config['links'][link_name] = link_val

		config['save']()
		return [{
			'title': 'Add URL',
			'description': 'The URL was successfully added:\n`%s`: %s' % (link_name, link_val),
		}]

	return [{
		'title': 'Error: Invalid Action',
		'color': 'red',
		'description': '`%s` is not a valid action. Please see `%shelp links` for a list of valid actions.' % (action, config['prefix']),
	}]
