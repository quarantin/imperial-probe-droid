import DJANGO
from swgoh.models import Player

from errors import *
from opts import parse_opts_ally_codes, parse_opts_mentions, parse_opts_lang, parse_opts_players
from swgohhelp import fetch_players

help_me = {
	'title': 'Me Help',
	'description': 'TODO',
}

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

def cmd_me(config, author, channel, args):

	args, selected_players, error = parse_opts_players(config, author, args)
	if error:
		return error

	if args:
		return error_unknown_parameters(args)

	lines = []
	for player in selected_players:

		author_str = author.id == player.discord_id and 'Your ally code' or ('Ally code of **<@%s>**' % player.discord_id)
		ally_code_str = Player.format_ally_code(player.ally_code)
		ally_code_full_str = '%s is **`%s`**.' % (author_str, ally_code_str)

		you_they_str = 'They'
		your_hisher_str = 'His/Her'
		if author.id == player.discord_id:
			you_they_str = 'You'
			your_hisher_str = 'Your'

		language = Player.get_language_info(player.language)
		language_str = '%s language is set to **%s** %s' % (your_hisher_str, language[3], language[2])

		lines.append(ally_code_full_str)
		lines.append(language_str)
		lines.append('')

	lines_str = '\n'.join(lines)
	return [{
		'title': 'Me',
		'description': 'Hello <@%s>,\n\n%s\nLanguage can be changed with **`%slanguage`**.' % (author.id, lines_str, config['prefix']),
	}]

async def fill_user_info(player):

	from bot import bot

	user = await bot.fetch_user(player.discord_id)
	for key, real_key in [ ('nick', 'discord_nick'), ('name', 'discord_name'), ('display_name', 'discord_display_name') ]:
		if hasattr(user, key):
			value = getattr(user, key)
			setattr(player, real_key, value)

async def register_users(config, author, discord_ids, ally_codes):

	if len(discord_ids) != len(ally_codes):
		return error_register_mismatch(config, author, discord_ids, ally_codes)

	lang = parse_opts_lang(author)
	language = Player.get_language_info(lang)

	players = fetch_players(config, {
		'allycodes': ally_codes,
		'project': {
			'name': 1,
			'allyCode': 1,
		},
	})

	lines = []
	for discord_id, ally_code in zip(discord_ids, ally_codes):

		db_player, created = Player.objects.get_or_create(discord_id=discord_id)

		game_nick = players[ally_code]['name']
		author_str = (author.id == discord_id) and 'Your ally code' or 'Ally code of **<@%s>**' % discord_id
		ally_code_str = Player.format_ally_code(ally_code)
		ally_code_full_str = '%s is **`%s`**.' % (author_str, ally_code_str)
		if db_player.ally_code and db_player.ally_code != ally_code:
			ally_code_full_str = '%s has changed from **`%s`** to **`%s`**.' % (author_str, db_player.get_ally_code(), ally_code_str)
		db_player.ally_code = ally_code
		db_player.game_nick = players[ally_code]['name']
		await fill_user_info(db_player)

		db_player.save()

		if created:
			registered_str = 'Registration successful for **<@%s>** alias **%s**!' % (discord_id, db_player.game_nick)
			lines.append(registered_str)

		lines.append(ally_code_full_str)
		lines.append('')

	you_they_str = 'They'
	your_hisher_str = 'His/Her'
	if len(discord_ids) == 1 and discord_ids[0] == author.id:
		you_they_str = 'You'
		your_hisher_str = 'Your'

	lines_str = '\n'.join(lines)

	return [{
		'title': '',
		'description': 'Hello <@%s>,\n\n%s%s language is set to **%s** %s.\n%s can change it with **`%slanguage`**.' % (author.id, lines_str, your_hisher_str, language[3], language[2], you_they_str, config['prefix']),
	}]

async def cmd_register(config, author, channel, args):

	lang = parse_opts_lang(author)
	language = Player.get_language_info(lang)

	discord_ids = parse_opts_mentions(config, author, args)
	ally_codes = parse_opts_ally_codes(config, author, args)

	if not ally_codes and len(discord_ids) < 2:
		try:
			p = Player.objects.get(discord_id=author.id)
			if p.ally_code not in ally_codes:
				ally_codes.append(p.ally_code)

		except Player.DoesNotExist:
			pass

	if not ally_codes:
		return error_no_ally_code_specified(config, author)

	if args:
		return error_unknown_parameters(args)

	if len(ally_codes) == len(discord_ids) + 1 and author.id not in discord_ids:
		discord_ids.append(author.id)

	return await register_users(config, author, discord_ids, ally_codes)
