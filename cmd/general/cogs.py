from tbcog import TBCog
from twcog import TWCog
from modscog import ModsCog
from ticketscog import TicketsCog

help_load = {
	'title': 'Load COG Help',
	'description': """Load COGs.

**Syntax**
```
%prefixload <cog>```
**Aliases**
```
%prefixl```
**Restrictions**
Only administrators of this bot can use this command.

**Examples**
Loading tickets cog:
```
%prefixload tickets```""",
}

help_unload = {
	'title': 'Unload COG Help',
	'description': """Unload COGs.

**Syntax**
```
%prefixunload <cog>```
**Aliases**
```
%prefixu```
**Restrictions**
Only administrators of this bot can use this command.

**Examples**
Unloading tickets cog:
```
%prefixunload tickets```""",

}

loadable_cogs = {
	'mods':    ModsCog,
	'tickets': TicketsCog,
	'tw':      TWCog,
	'tb':      TBCog,
}

def parse_opts_cogs(args):

	cogs = []
	args_cpy = list(args)
	for arg in args_cpy:
		larg = arg.lower()
		if larg in loadable_cogs:
			args.remove(arg)
			cogs.append(loadable_cogs[larg])

	return cogs

def cmd_unload(request):

	bot = request.bot
	args = request.args
	author = request.author
	config = request.config

	if 'admins' not in config or author.id not in config['admins']:
		return bot.errors.error_permission_denied()

	cogs = parse_opts_cogs(args)
	for cog in cogs:
		bot.remove_cog(cog.__name__)

	plural = len(cogs) > 1 and 's' or ''
	plural_have = len(cogs) > 1 and 'have' or 'has'
	return [{
		'title': 'Load Cog',
		'description': 'The following cog%s %s been successfully unloaded:\n%s' % (plural, plural_have, '\n'.join([ cog.__name__ for cog in cogs ])),
	}]

def cmd_load(request):

	bot = request.bot
	args = request.args
	author = request.author
	config = request.config

	if 'admins' not in config or author.id not in config['admins']:
		return bot.errors.error_permission_denied()

	cogs = parse_opts_cogs(args)

	if args:
		return bot.errors.error_unknown_parameters(args)

	if not cogs:
		cogs = list(loadable_cogs.values())

	for cog in cogs:
		bot.add_cog(cog(bot))

	plural = len(cogs) > 1 and 's' or ''
	plural_have = len(cogs) > 1 and 'have' or 'has'
	return [{
		'title': 'Load Cog',
		'description': 'The following cog%s %s been successfully loaded:\n%s' % (plural, plural_have, '\n'.join([ cog.__name__ for cog in cogs ])),
	}]

