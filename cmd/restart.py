#!/usr/bin/python3

help_restart = {
	'title': 'Restart Help',
	'description': """Restart this bot.
	
**Syntax**
```
%prefixrestart```

**Aliases**
```
%prefixR```

**Restrictions**
Only administrators of this bot can use this command.

**Examples**
```
%prefixR
%prefixrestart```""",
}

def cmd_restart(config, author, channel, args):

	if 'admins' in config and author in config['admins']:
		exit_bot()

	return [{
		'title': 'Unauthorized Command',
		'color': 'red',
		'description': 'You are not allowed to run this command because you are not an administrator.',
	}]
