#!/usr/bin/python3

from errors import *

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
Restart the bot:
```
%prefixR```""",
}

def cmd_restart(config, author, channel, args):

	if 'admins' in config and author.id in config['admins']:
		from utils import exit_bot
		exit_bot()
		return []

	return error_permission_denied()
