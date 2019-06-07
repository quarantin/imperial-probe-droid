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
		config['bot'].exit()
		return []

	return error_permission_denied()
