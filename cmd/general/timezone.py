from opts import *

import DJANGO
from swgoh.models import Player

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

async def cmd_timezone(ctx):

	bot = ctx.bot
	args = ctx.args
	config = ctx.config

	selected_players, error = parse_opts_players(ctx, max_allies=1)

	if error:
		return error

	if not selected_players:
		return bot.errors.error_no_ally_code_specified(ctx)

	timezones = parse_opts_timezones(ctx)
	if args:
		return bot.errors.error_unknown_parameters(args)

	player = selected_players[0]

	if not timezones:
		timezones_url = '%s/media/timezones.txt' % config.get_server_url()
		return [{
			'title': 'Available Timezones',
			'description': 'Your timezone is set to **%s**.\n%s\nThe list of supported timezones can be found [here](%s)' % (player.timezone, config['separator'], timezones_url),
		}]

	if len(timezones) > 1:
		return [{
			'title': 'More than one timezone selected',
			'description': 'You cannot supply more than one timezone but we found %d:\n- %s' % (len(timezones), '\n- '.join(timezones)),
		}]

	player.timezone = timezones[0]
	player.save()

	return [{
		'title': 'Operation Successful',
		'description': 'Timezone for <@%s> has been changed to **%s**.' % (player.discord_id, player.timezone),
	}]
