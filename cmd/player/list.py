from utils import translate

help_list = {
	'title': 'List Help',
	'description': """List character or ship names.

**Syntax**
```
%prefixlist [units or factions]```
**Examples**
List all bounty hunters:
```
%prefixlist bh```
List Darth Malak and both Revan:
```
%prefixlist malak revan```"""
}

def cmd_list(ctx):

	bot = ctx.bot
	args = ctx.args
	config = ctx.config

	language = bot.options.parse_lang(ctx, args)

	selected_units = bot.options.parse_unit_names(args)

	if args:
		return bot.errors.unknown_parameters(args)

	if not selected_units:
		return bot.errors.no_unit_selected(ctx)

	msgs = []
	translations = []
	for unit in selected_units:
		name = translate(unit.base_id, language)
		translations.append(name)

	unit_list = '\n- '.join(translations)
	return [{
		'title': 'Unit List',
		'description': 'Here is the list of units you selected:\n- %s\n' % unit_list,
	}]
