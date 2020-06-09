import pytz
from datetime import datetime, timedelta

help_lastseen = {
	'title': 'Last Seen Help',
	'description': """Shows when a player was last seen in the game.

**Syntax**
```
%prefixlastseen [players]```
**Aliases**
```
%prefixlast
%prefixseen```"""
}

async def cmd_lastseen(ctx):

	bot = ctx.bot
	args = ctx.args
	config = ctx.config

	selected_players, error = bot.options.parse_players(ctx, args)

	ally_codes = [ player.ally_code for player in selected_players ]
	players = await bot.client.players(ally_codes=ally_codes)
	if not players:
		return bot.errors.ally_codes_not_found(ally_codes)

	players = { x['allyCode']: x for x in players }

	last_seen = {}

	for ally_code, player in players.items():

		ts = int(int(player['updated']) / 1000)
		timedelta = datetime.now(pytz.utc) - pytz.utc.localize(datetime.fromtimestamp(ts))

		player_name = player['name']
		last_seen[player_name] = timedelta

	lines = []
	for player_name, timedelta in sorted(last_seen.items(), key=lambda x: x[1]):
		timedeltastr = str(timedelta).split('.')[0]
		lines.append('%s was last seen %s ago.' % (player['name'], timedeltastr))

	return [{
			'title': 'Last Seen',
			'description': '\n'.join(lines),
	}]
