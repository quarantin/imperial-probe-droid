
help_invite = {
	'title': 'Invite Help',
	'description': """Invite this bot to your discord server.
	
**Syntax**
```
%prefixinvite```""",
}

def cmd_invite(request):

	config = request.config

	return [{
		'title': 'Invite Imperial Probe Droid',
		'description': '%s\n[Invite this bot to your server](%s)' % (config['separator'], config['invite']),
	}]
