from config import get_perms
from urllib.parse import urlencode

help_invite = {
	'title': 'Invite Help',
	'description': """Invite this bot to your discord server.
	
**Syntax**
```
%prefixinvite```
If the link is not working for you, please try:
```
%prefixinvite link```""",
}

def cmd_invite(request):

	args = request.args
	config = request.config

	invite_url = 'https://discordapp.com/api/oauth2/authorize?' + urlencode({
		'client_id': config['bot'].user.id,
		'perms': get_perms(),
		'scope': 'bot',
	})

	invite_msg = 'Click here to invite this bot to your server'
	invite_link = '[%s](%s)' % (invite_msg, invite_url)
	if 'link' in args:
		invite_link = invite_url

	return [{
		'title': 'Invite Imperial Probe Droid',
		'description': '%s\n%s' % (config['separator'], invite_link),
	}]
