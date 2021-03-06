from utils import translate

import DJANGO
from swgoh.models import BaseUnit

help_locked = {
	'title': 'Locked Help',
	'description': """Shows characters and ships that are still locked for the supplied players.

**Syntax**
```
%prefixlocked [players] [options]```
**Aliases**
```
%prefixl```
**Options**
The following options are available to filter output:
**`chars`** (or **`c`**): To show locked characters for the specified players.
**`ships`** (or **`s`**): To show locked ships for the specificed players.
If no options are specified, all locked characters and ships are displayed.

**Examples**
Show your locked characters and ships:
```
%prefixl```
Show only your locked characters:
```
%prefixl c```
Show only your locked ships:
```
%prefixl ships```
Show locked characters and ships for someone by mention:
```
%prefixl @Someone```
Show locked characters and ships for someone by discord-nick (no hilight):
```
%prefixl "Someone"```
Show locked characters for someone by ally code:
```
%prefixl 123456789 chars```
Show locked characters and ships for two different ally codes:
```
%prefixl 123456789 234567891```"""
}
	
async def cmd_locked(ctx):

	bot = ctx.bot
	args = ctx.args
	config = ctx.config

	ctx.alt = bot.options.parse_alt(args)
	language = bot.options.parse_lang(ctx, args)

	selected_players, error = bot.options.parse_players(ctx, args)

	selected_opts = bot.options.parse_locked(args)

	if error:
		return error

	if not selected_players:
		return bot.errors.no_ally_code_specified(ctx)

	if args:
		return bot.errors.unknown_parameters(args)

	ally_codes = [ player.ally_code for player in selected_players ]
	players = await bot.client.players(ally_codes=ally_codes)
	if not players:
		return bot.errors.ally_codes_not_found(ally_codes)

	players = { x['allyCode']: x for x in players }

	units = BaseUnit.get_all_units()
	ships = BaseUnit.get_all_ships()
	char_list = { x.base_id: x for x in units }
	ship_list = { x.base_id: x for x in ships }

	msgs = []
	lines = []
	for ally_code, player in players.items():

		ally_units = { x['defId']: x for x in player['roster'] }

		if selected_opts in [ 'chars', 'all' ]:

			locked_chars = []
			for base_id, char in char_list.items():
				if base_id not in ally_units:
					char_name = translate(base_id, language)
					locked_chars.append(char_name)

			if not locked_chars:
				locked_chars.append('All characters unlocked!')

			lines.append('**Locked Characters**')
			lines += sorted(locked_chars)
			lines.append('')

		if selected_opts in [ 'ships', 'all' ]:

			locked_ships = []
			for base_id, ship in ship_list.items():
				if base_id not in ally_units:
					ship_name = translate(base_id, language)
					locked_ships.append(ship_name)

			if not locked_ships:
				locked_ships.append('All ships unlocked!')

			lines.append('**Locked Ships**')
			lines += sorted(locked_ships)
			lines.append('')

		msgs.append({
			'author': {
				'name': '%s\'s Locked Units' % player['name'],
			},
			'title': '',
			'description': '\n'.join(lines),
		})

	return msgs
