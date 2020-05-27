import pytz
from datetime import datetime

help_clock = {
	'title': 'Clock Help',
	'description': """Shows current time in different timezones.
	
**Syntax**
```
%prefixclock [timezone]```
**Examples**
Show current time for the most common timezones:
```
%prefixclock```
Show current time for Paris and New York:
```
%prefixclock Europe/Paris America/New_York```
Or more simply:
```
%prefixclock paris new york```""",
}

TIMEZONES = [
	'US/Pacific',
	'US/Central',
	'US/Eastern',
	'UTC',
	'Europe/London',
	'Europe/Paris',
	'Australia/Sydney',
]

def cmd_clock(ctx):

	bot = ctx.bot
	args = ctx.args
	all_timezones = list(TIMEZONES)

	timezones = bot.options.parse_timezones(args)

	if args:
		return bot.errors.unknown_parameters(args)

	if timezones:
		all_timezones = timezones

	lines = []
	now = datetime.now(pytz.utc)
	for tzname in all_timezones:
		tzinfo = pytz.timezone(tzname)
		date = datetime(year=now.year, month=now.month, day=now.day, hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond, tzinfo=pytz.utc)
		lines.append('%s %s' % (date.astimezone(tzinfo).strftime('%H:%M'), tzname))

	description = '\n'.join(lines)
	return [{
		'title': 'Clock',
		'description': '```%s```' % description,
	}]
