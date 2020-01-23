from config import get_perms
from urllib.parse import urlencode

help_invite = {
	'title': 'Invite Help',
	'description': """Invite this bot to your discord server.
	
**Syntax**
```
%prefixinvite```""",
}

def cmd_invite(request):

	config = request.config

	invite_url = 'https://discordapp.com/api/oauth2/authorize?' + urlencode({
		'client_id': config['bot'].user.id,
		'perms': get_perms(),
		'scope': 'bot',
	})

	return [{
		'title': 'Invite Imperial Probe Droid',
		'description': '%s\n[Invite this bot to your server](%s)' % (config['separator'], invite_url),
	}]
