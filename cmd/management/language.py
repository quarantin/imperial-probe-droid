import DJANGO
from swgoh.models import Player

from errors import *
from opts import parse_opts_players, parse_opts_language

help_language = {
	'title': 'Language Help',
	'description': """Configure your preferred language.
	
**Syntax**
```
%prefixlanguage [language code]```

**Examples**
List available languages:
```
%prefixlanguage```
Configure your default language to French:
```
%prefixlanguage fr```""",
}

def get_available_languages(config, author):
	langs = [ ' - **%s**: %s' % (lang_code, lang_name) for language, lang_code, lang_flag, lang_name in Player.LANGS ]
	langs.insert(0, 'Here is the list of supported languages:')

	try:
		player = Player.objects.get(discord_id=author.id)
		language = Player.get_language_info(player.language)
		langs.insert(0, 'Your current language is **%s** %s' % (language[3], language[2]))
		langs.insert(1, config['separator'])

	except Player.DoesNotExist:
		pass

	return [{
		'title': 'Available Languages',
		'description': '%s' % '\n'.join(langs),
	}]

def cmd_language(config, author, channel, args):

	args, players, error = parse_opts_players(config, author, args, max_allies=1)

	args, language = parse_opts_language(args)

	if args:
		return error_unknown_parameters(args)

	if not language:
		return get_available_languages(config, author)

	if not players:
		return error

	player = players[0]
	player.language = language[0]
	player.save()

	return [{
		'title': 'Operation Successful',
		'description': 'The language settings for <@%s> have been changed to **%s** %s.' % (player.discord_id, language[3], language[2]),
	}]
