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

def do_ban(ctx, banned):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	config = ctx.config

	if 'admins' not in config or author.id not in config['admins']:
		return bot.errors.permission_denied()

	ctx.alt = bot.options.parse_alt(args)
	selected_players, error = bot.options.parse_players(ctx, args, exclude_author=True)

	if error:
		return error

	if not selected_players:
		return bot.errors.no_ally_code_specified_ban(ctx)

	if args:
		return bot.errors.unknown_parameters(args)

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

def cmd_ban(ctx):
	return do_ban(ctx, True)

def cmd_unban(ctx):
	return do_ban(ctx, False)
