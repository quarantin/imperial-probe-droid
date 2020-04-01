from utils import get_invite_link, get_invite_url

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

	invite_link = get_invite_link(config)
	if 'link' in args:
		invite_link = get_invite_url(config)

	return [{
		'title': 'Invite Imperial Probe Droid',
		'description': '%s\n%s' % (config['separator'], invite_link),
	}]
