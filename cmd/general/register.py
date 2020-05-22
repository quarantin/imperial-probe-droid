from opts import parse_opts_ally_codes, parse_opts_mentions, parse_opts_lang, parse_opts_players

import DJANGO
from swgoh.models import Player

help_me = {
	'title': 'Me Help',
	'description': 'TODO',
}

help_register = {
	'title': 'Register Help',
	'description': """Register yourself or your teammates to the bot.
	
**Syntax**
Self registration:
```
%prefixregister <ally-code>```
Mass registration:
```
%prefixregister <players> <ally-codes>```
**Examples**
Register your ally code:
```
%prefixregister 123456789
%prefixregister 234-567-891```
Register two players at once:
```
%prefixregister @somePlayer @otherPlayer 123456789 234567891
%prefixregister @somePlayer @otherPlayer 123-456-789 234-567-891```""",
}

def cmd_me(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	config = ctx.config

	selected_players, error = parse_opts_players(ctx)
	if error:
		return error

	if args:
		return bot.errors.error_unknown_parameters(args)

	lines = []
	for player in selected_players:

		author_str = 'Ally code of **<@%s>**' % player.discord_id
		ally_code_full_str = '%s is **`%s`**.' % (author_str, Player.format_ally_code(player.ally_code))
		lines.append(ally_code_full_str)
		lines.append('')

		language = Player.get_language_info(player.language)
		lines.append('Your language is set to **%s** %s.' % (language[3], language[2]))
		lines.append('Please type **`%slanguage`** to change your language.' % config['prefix'])
		lines.append('')

		timezone = player.timezone or 'Europe/London'
		lines.append('Your timezone is set to **%s**.' % timezone)
		lines.append('Please type **`%stimezone`** to change your timezone.' % config['prefix'])
		lines.append('')

	lines_str = '\n'.join(lines)
	return [{
		'title': '',
		'description': 'Hello <@%s>,\n\n%s\n' % (author.id, lines_str),
	}]

async def fill_user_info(config, player):

	user = await config['bot'].fetch_user(player.discord_id)
	for key, real_key in [ ('nick', 'discord_nick'), ('name', 'discord_name'), ('display_name', 'discord_display_name') ]:
		if hasattr(user, key):
			value = getattr(user, key)
			setattr(player, real_key, value)

async def register_users(ctx, discord_ids, ally_codes):

	bot = ctx.bot
	author = ctx.author
	config = ctx.config

	if len(discord_ids) != len(ally_codes):
		return bot.errors.error_register_mismatch(ctx, discord_ids, ally_codes)

	lang = parse_opts_lang(ctx)
	language = Player.get_language_info(lang)

	players = await bot.client.players(ally_codes=ally_codes)
	players = { x['allyCode']: x for x in players }

	lines = []
	for discord_id, ally_code in zip(discord_ids, ally_codes):

		jplayer = players[ally_code]

		db_player, created = Player.objects.get_or_create(discord_id=discord_id)

		author_str = 'Ally code of **<@%s>**' % discord_id
		ally_code_str = Player.format_ally_code(ally_code)
		ally_code_full_str = '%s is **`%s`**.' % (author_str, ally_code_str)
		if db_player.ally_code and db_player.ally_code != ally_code:
			ally_code_full_str = '%s has changed from **`%s`** to **`%s`**.' % (author_str, db_player.get_ally_code(), ally_code_str)
		db_player.ally_code   = ally_code
		db_player.timezone    = 'Europe/London'
		db_player.player_id   = jplayer['id']
		db_player.player_name = jplayer['name']
		await fill_user_info(config, db_player)

		db_player.save()

		registered_str = 'Player **%s** already registered!' % db_player.player_name
		if created:
			registered_str = 'Registration successful for **%s**!' % db_player.player_name

		lines.append(registered_str)
		lines.append(ally_code_full_str)
		lines.append('')

		#language = Player.get_language_info(db_player.language)
		#lines.append('Your language is set to **%s** %s.' % (language[3], language[2]))
		#lines.append('Please type **`%slanguage`** to change your language.' % config['prefix'])
		#lines.append('')

		#timezone = db_player.timezone or 'Europe/London'
		#lines.append('Your timezone is set to **%s**.' % timezone)
		#lines.append('Please type **`%stimezone`** to change your timezone.' % config['prefix'])
		#lines.append('')

	lines_str = '\n'.join(lines)

	return [{
		'title': 'Register',
		'description': 'Hello <@%s>,\n\n%s' % (author.id, lines_str),
	}]

async def cmd_register(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	config =  ctx.config

	lang = parse_opts_lang(ctx)
	language = Player.get_language_info(lang)

	discord_ids = parse_opts_mentions(ctx)
	ally_codes = parse_opts_ally_codes(ctx)

	if not ally_codes and len(discord_ids) < 2:
		try:
			p = Player.objects.get(discord_id=author.id)
			if p.ally_code not in ally_codes:
				ally_codes.append(p.ally_code)

		except Player.DoesNotExist:
			pass

	if not ally_codes:
		return bot.errors.error_no_ally_code_specified(ctx)

	if args:
		return bot.errors.error_unknown_parameters(args)

	if len(ally_codes) == len(discord_ids) + 1 and author.id not in discord_ids:
		discord_ids.append(author.id)

	return await register_users(ctx, discord_ids, ally_codes)
