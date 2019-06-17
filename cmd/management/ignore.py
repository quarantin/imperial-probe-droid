from errors import *

help_ignore = {
	'title': 'Ignore Help',
	'description': """Ignore some commands.
	
**Syntax**
List ignored commands:
```
%prefixignore```
Add command to ignore:
```
%prefixignore add <command>```
Remove command from ignored list:
```
%prefixignore del <command>```""",
}

def cmd_ignore(config, author, channel, args):

	if 'admins' not in config or author.id not in config['admins']:
		return error_permission_denied()

	lines = []
	if not args:

		i = 1
		for cmd in config['ignored']:
			lines.append('**[%d]** `%s`' % (i, cmd))
			i += 1

		return [{
			'title': 'Ignored List',
			'description': '\n'.join(lines),
		}]

	action = args.pop(0).lower()

	if action == 'del':
		return []

	elif action == 'add':
		return []

	else:
		return [{
			'title': 'Error: Invalid Action',
			'description': '`%s` is not a valid action. Please type `%shelp ignore` for a list of valid actions.' % (action, config['prefix']),
		}]
