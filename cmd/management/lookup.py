#!/usr/bin/python3

from errors import *

help_lookup = {
	'title': 'Lookup Help',
	'description': """Lookup a discord user accross all servers this bot is connected to.
	
**Syntax**
```
%prefixlookup <discord id>```
**Restrictions**
Only administrators of this bot can use this command.```"""
}

def cmd_lookup(config, author, channel, args):

	if 'admins' not in config or author.id not in config['admins']:
		return error_permission_denied()

	from bot import bot
	for server in bot.servers:
		for member in server.members:

			display_name = ''
			if hasattr(member, 'display_name') and member.display_name:
				display_name = member.display_name

			nick = ''
			if hasattr(member, 'nick') and member.nick:
				nick = member.nick

			name = ''
			if hasattr(member, 'name') and member.name:
				name = member.name

			for arg in args:
				if arg in member.id or arg in display_name or arg in nick or arg in name:
					print('server:%s id:%s display_name:%s nick:%s name:%s' % (member.server, member.id, display_name, nick, name))
	return []
