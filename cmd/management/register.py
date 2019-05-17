#!/usr/bin/python3

import DJANGO
from swgoh.models import Player

from errors import *
from opts import parse_opts_players

help_register = {
	'title': 'Register Help',
	'description': """Register your ally code.
	
**Syntax**
```
%prefixregister <ally-code>```

**Examples**
Register your ally code:
```
%prefixregister 123456789
%prefixregister 123-456-789```""",
}

def cmd_register(config, author, channel, args):

	args, players, error = parse_opts_players(config, author, args, min_allies=1, max_allies=1)
	if args:
		return error_unknown_parameters(args)

	if not players:
		return error

	new_user = True
	db_player = None
	player = players[0]
	try:
		db_player = Player.objects.get(discord_id=author.id)
		new_user = False

	except Player.DoesNotExist:
		pass

	your_ally_code = 'Here is your ally code: **%s**\n' % player.get_ally_code()
	if db_player and player.ally_code != db_player.ally_code:
		ally_code = player.ally_code
		your_ally_code = 'Your ally code has been changed from **%s** to **%s**.\n' % (db_player.get_ally_code(), player.get_ally_code())
		player = db_player
		player.ally_code = ally_code

	if hasattr(author, 'name'):
		player.discord_name=author.name

	if hasattr(author, 'nick'):
		player.discord_nick=author.nick

	if hasattr(author, 'display_name'):
		player.discord_display_name=author.display_name

	player.save()

	language = Player.get_language_info(player.language)
	registered = new_user and 'Registration successful!\n' or ''

	return [{
		'title': '',
		'description': 'Hello <@%s>,\n%s%s\nYour current language is set to **%s** %s.\nYou can change it with `%slanguage`.' % (player.discord_id, registered, your_ally_code, language[3], language[2], config['prefix']),
	}]
