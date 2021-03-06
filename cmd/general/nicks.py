help_nicks = {
	'title': 'Nicks Help',
	'description': """Handles the list of nicknames (list/add/delete) for units and ships.

**Syntax**
```
%prefixnicks
%prefixnicks add [nick] [unit or ship]
%prefixnicks del [nick or nick ID]```
**Aliases**
```
%prefixN```
**Examples**
To list all registered character nicks:
```
%prefixN```
Add nick **ep** for **Emperor Palpatine**:
```
%prefixN add ep palpatine```
Add nick **gat** for **Grand Admiral Thrawn**:
```
%prefixN add gat thrawn```
Delete nick **gat**:
```
%prefixN del gat```
Delete first nick (**ep**) using its ID:
```
%prefixN del 1```"""
}

def cmd_nicks(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	config = ctx.config

	lines = []
	prefix = config['prefix']

	if not args:

		i = 1
		for nick, name in sorted(config['nicks'].items()):
			lines.append('**[%d]** **%s** `%s`' % (i, nick, name))
			i += 1

		return [{
			'title': 'Character Nick List',
			'description': '\n'.join(lines),
		}]

	if 'admins' not in config or author.id not in config['admins']:
		return bot.errors.permission_denied()

	action = args.pop(0)

	if action == 'del':

		if len(args) < 1:
			return bot.errors.missing_parameters(ctx, 'nicks')

		target_nick = args.pop(0)
		if target_nick.isdigit():
			target_nick = int(target_nick)

			i = 1
			for nick, name in sorted(config['nicks'].items()):
				if i == target_nick:
					old_nick = nick
					old_unit = name
					del config['nicks'][nick]
					break

				i = i + 1
		elif target_nick in config['nicks']:
			old_nick = target_nick
			old_unit = config['nicks'][target_nick]
			del config['nicks'][target_nick]

		config['save']()
		return [{
			'title': 'Delete Nick',
			'description': 'The nickname was successfully deleted:\n`%s`: %s' % (old_nick, old_unit),
		}]

	elif action == 'add':

		if len(args) < 2:
			return bot.errors.missing_parameter(ctx, 'nicks')

		target_nick = args.pop(0)
		selected_units = bot.options.parse_unit_names(args)
		if args:
			return bot.errors.unknown_parameters(args)

		if not selected_units:
			return bot.errors.no_unit_selected(ctx)

		if len(selected_units) > 1:
			return [{
				'title': 'Error: Invalid Number of Units',
				'color': 'red',
				'description': 'You provided %d units but you have to supply only one.' % len(selected_units)
			}]

		config['nicks'][target_nick] = selected_units.pop(0).name

		config['save']()
		return [{
			'title': 'Add Nick',
			'description': 'The nickname was successfully added:\n`%s`: %s' % (target_nick, config['nicks'][target_nick]),
		}]

	return [{
		'title': 'Error: Invalid Action',
		'description': '`%s` is not a valid action. Please type `%shelp nicks` for a list of valid actions.' % (action, config['prefix']),
	}]
