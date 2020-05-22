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

	bot = request.bot
	args = request.args
	config = request.config

	invite_link = bot.get_invite_link()
	if 'link' in args:
		invite_link = bot.get_invite_url()

	return [{
		'title': 'Invite Imperial Probe Droid',
		'description': '%s\n%s' % (config['separator'], invite_link),
	}]
