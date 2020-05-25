help_lookup = {
	'title': 'Lookup Help',
	'description': """Lookup a discord user accross all servers this bot is connected to.
	
**Syntax**
```
%prefixlookup <discord id>|<discord nick```
**Restrictions**
Only administrators of this bot can use this command.```"""
}

def cmd_lookup(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	config = ctx.config

	if 'admins' not in config or author.id not in config['admins']:
		return bot.errors.permission_denied()

	for server in config['bot'].guilds:
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
				arg = arg.lower()
				if arg == str(member.id) or arg in display_name.lower() or arg in nick.lower() or arg in name.lower():
					print('FOUND: server:%s id:%s display_name:%s nick:%s name:%s' % (member.guild, member.id, display_name, nick, name))
	print('Done.')
	return []
