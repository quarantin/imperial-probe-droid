from utils import exit_bot

help_invite = {
	'title': 'Invite Help',
	'description': """Invite this bot to your discord server.
	
**Syntax**
```
%prefixinvite```
**Aliases**
```
%prefixI```

**Examples**
```
%prefixI
%prefixinvite```""",
}

def cmd_invite(config, author, channel, args):

	return [{
		'title': 'Invite Imperial Probe Droid',
		'description': '%s\n[Invite this bot to your server](%s)' % (config['separator'], config['invite']),
	}]
