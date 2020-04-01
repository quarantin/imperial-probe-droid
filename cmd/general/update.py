from errors import *

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
Update the bot:
```
%prefixu```"""
}

def cmd_update(request):

	author = request.author
	config = request.config

	if 'admins' in config and author.id in config['admins']:
		from utils import update_source_code
		update_source_code()
		config['bot'].exit()
		return []

	return error_permission_denied()
