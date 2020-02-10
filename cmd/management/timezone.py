import DJANGO
from swgoh.models import Player

from opts import *
from errors import *

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

async def cmd_timezone(request):

	args = request.args
	config = request.config

	players, error = parse_opts_players(request, max_allies=1)
	if not players:
		return error

	timezone = parse_opts_timezone(request)
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
