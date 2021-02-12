help_restart = {
	'title': 'Restart Help',
	'description': """Restart this bot.
	
**Syntax**
```
%prefixrestart```
**Aliases**
```
%prefixR```
**Restrictions**
Only administrators of this bot can use this command.

**Examples**
Restart the bot:
```
%prefixR```""",
}

def cmd_restart(ctx):

	bot = ctx.bot
	author = ctx.author
	config = ctx.config

	if 'admins' in config and author.id in config['admins']:
		bot.exit()
		return []

	return bot.errors.permission_denied()
