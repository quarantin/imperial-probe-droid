help_servers = {
	'title': 'Servers Help',
	'description': """List all discord servers where this bot is connected.

**Syntax**
```
%prefixservers```
**Restrictions**
Only administrators of this bot can use this command.```"""
}

def cmd_servers(ctx):

	bot = ctx.bot
	author = ctx.author
	config = ctx.config

	if 'admins' not in config or author.id not in config['admins']:
		return bot.errors.permission_denied()

	servers = []
	for server in config['bot'].guilds:
		servers.append(server.name)

	return [{
		'title': 'Connected to %d Servers' % len(servers),
		'description': '\n - '.join(servers),
	}]
