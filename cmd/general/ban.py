from opts import *
from errors import *

import DJANGO
from swgoh.models import Player

help_ban = {
	'title': 'Ban Help',
	'description': """Ban players from using this bot.
	
**Syntax**
Ban a player by mention:
```
%prefixban @Someone```
Ban a player by allycode:
```
%prefixban 123456789```""",
}

help_unban = {
	'title': 'Unban Help',
	'description': """Unban players from using this bot.
	
**Syntax**
Unban a player by mention:
```
%prefixunban @Someone```
Unban a player by allycode:
```
%prefixunban 123456789```""",
}

def do_ban(request, banned):

	args = request.args
	author = request.author
	config = request.config

	if 'admins' not in config or author.id not in config['admins']:
		return error_permission_denied()

	selected_players, error = parse_opts_players(request, exclude_author=True)
	if error:
		return error

	if not selected_players:
		return error_no_ally_code_specified_ban(config)

	if args:
		return error_unknown_parameters(args)

	banned_players = []
	for player in selected_players:
		player.banned = banned
		player.save()

		if player.discord_id:
			banned_players.append('<@%s>' % player.discord_id)

		elif player.ally_code:
			banned_players.append(str(player.ally_code))

		else:
			banned_players.append(str(player))

	plural = len(banned_players) > 1 and 's' or ''
	plural_have = len(banned_players) > 1 and 'have' or 'has'
	strbanned = banned and 'banned' or 'unbanned'

	return [{
		'title': 'Banned Players',
		'description': 'The following player%s %s been **%s**:\n%s' % (plural, plural_have, strbanned, '\n'.join(banned_players)),
	}]

def cmd_ban(request):
	return do_ban(request, True)

def cmd_unban(request):
	return do_ban(request, False)
