#!/usr/bin/python3

from utils import exit_bot, update_source_code

help_update = {
	'title': 'Update Help',
	'description': """Update the source code and restart this bot.
	
**Syntax**
```
%prefixupdate```

**Aliases**
```
%prefixU```

**Restrictions**
Only administrators of this bot can use this command.

**Examples**
```
%prefixu
%prefixupdate```""",
}

def cmd_update(config, author, channel, args):

	if 'admins' in config and author in config['admins']:
		update_source_code()
		exit_bot()

	return [{
		'title': 'Unauthorized Command',
		'color': 'red',
		'description': 'You are not allowed to run this command because you are not an administrator.',
	}]
