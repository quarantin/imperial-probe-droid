import DJANGO
from swgoh.models import Player

from errors import *
from opts import parse_opts_players

help_timezone = {
	'title': 'Timezone Help',
	'description': """Configure your timezone.
	
**Syntax**
```
%prefixtimezone [timezone]```

**Examples**
List available timezones:
```
%prefixtimezone```
Set your timezone to Paris:
```
%prefixtimezone Europe/Paris```
Set your timezone to New York:
```
%prefixtimezone America/New_York```""",
}

def get_available_timezones():

	from pytz import common_timezones

	timezones = list(common_timezones)

	# We don't want users to select GMT or UTC because these
	# timezones don't take daylight saving times into account.
	timezones.remove('GMT')
	timezones.remove('UTC')

	return timezones

def parse_opts_timezone(args):

	args_cpy = list(args)

	timezones = get_available_timezones()

	for arg in args_cpy:

		larg = arg.lower()
		for tz in timezones:

			tzl = tz.lower()
			if tzl == larg:
				args.remove(arg)
				return args, tz

			tokens = tzl.split('/')
			if len(tokens) == 2 and larg == tokens[1]:
				args.remove(arg)
				return args, tz

	return args, None

async def cmd_timezone(config, author, channel, args):

	args, players, error = parse_opts_players(config, author, args, max_allies=1)
	if not players:
		return error

	args, timezone = parse_opts_timezone(args)
	if args:
		return error_unknown_parameters(args)

	player = players[0]

	if not timezone:
		timezones_url = 'http://%s/media/timezones.txt' % config['server']
		return [{
			'title': 'Available Timezones',
			'description': 'Your timezone is set to **%s**.\n%s\nThe list of supported timezones can be found [here](%s)' % (player.timezone, config['separator'], timezones_url),
		}]

	player.timezone = timezone
	player.save()

	return [{
		'title': 'Operation Successful',
		'description': 'Timezone for <@%s> has been changed to **%s**.' % (player.discord_id, timezone),
	}]
