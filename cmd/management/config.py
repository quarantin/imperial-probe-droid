from errors import *

help_config = {
	'title': 'Config Help',
	'description': """Configure various settings of the bot per discord server.
	
**Syntax**
```
%prefixconfig prefix <custom prefix>```
**Examples**
To change prefix to '?':
```
%prefixconfig prefix ?```
In case of invalid/unknown prefix, you can still address the bot using discord mentions."""
}

def cmd_config(config, author, channel, args):

	import DJANGO
	from swgoh.models import DiscordServer

	server_id = channel.guild.id
	try:
		server = DiscordServer.objects.get(server_id=server_id)
	except DiscordServer.DoesNotExist:
		server = DiscordServer(server_id=server_id, bot_prefix=config['prefix'])

	if len(args) == 1 and args[0].lower() == 'prefix':
		return [{
			'title': 'Config Bot Prefix',
			'description': "Current bot prefix is '%s'" % server.bot_prefix,
		}]

	if len(args) == 2 and args[0].lower() == 'prefix':
		new_prefix = args[1].lower().strip()
		if not new_prefix:
			return [{
				'title': 'Error: Invalid bot prefix',
				'color': 'red',
				'description': 'The supplied bot prefix (%s) is not valid.' % new_prefix,
			}]

		server.bot_prefix = new_prefix
		server.save()
		return [{
			'title': 'Config Bot Prefix',
			'description': "Bot prefix has been changed to '%s'" % server.bot_prefix,
		}]

	return [{
		'title': 'Error: Invalid Parameters',
		'color': 'red',
		'description': 'Please type `%shelp config` to get help about this command.' % server.bot_prefix,
	}]
