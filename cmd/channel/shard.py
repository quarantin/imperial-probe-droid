from opts import *
from errors import *
from swgohhelp import api_swgoh_players

from swgoh.models import Player, Shard, ShardMember

import pytz
from datetime import datetime, timedelta

help_shard = {
	'title': 'Shard Help',
	'description': """Helps you to track the ranks and payout time of your shard members over time in arena.

**Syntax**
Creating a shard channel for character arena:
```
%prefixshard create char```
Creating a shard channel for fleet arena:
```
%prefixshard create ship```
Adding members to your shard:
```
%prefixshard add [players]```
Removing members from your shard:
```
%prefixshard del [players]```
Setting payout time for one of your shard member:
```
%prefixshard payout HH:MM [players]```
Showing arena rank and payout time of your shard members:
```
%prefixshard```
Exporting ally codes from your shard:
```
%prefixshard export```
**Examples**
Create a channel for your character arena shard:
```
%prefixshard create char```
Add some members to your shard:
```
%prefixshard add 123456789 234567891 345-678-912```
Remove some members from your shard:
```
%prefixshard del 123-456-789 234567891 345678912```
List arena ranks of all members of your shard:
```
%prefixshard```
Set payout time for two of your shard members:
```
%prefixshard payout 18:00 123456789 234567891```
Export ally codes from your shard:
```
%prefixshard export```"""
}

def get_payout_times(shard):

	res = {}
	members = ShardMember.objects.filter(shard=shard)
	for member in members:
		res[member.ally_code] = member.payout_time

	return res

def parse_opts_shard_type(args):

	args_cpy = list(args)
	for arg in args_cpy:

		larg = arg.lower()
		if larg in shard_types:
			args.remove(arg)
			return shard_types[larg]

	return None

def parse_opts_payout_time(tz, args):

	import re

	args_cpy = list(args)

	for arg in args_cpy:
		result = re.match('^[0-9][0-9]:[0-9][0-9]$', arg)
		if result:
			args.remove(arg)
			now = datetime.now(tz)
			tokens = result[0].split(':')
			return now.replace(hour=int(tokens[0]), minute=int(tokens[1]), second=0, microsecond=0).astimezone(pytz.utc)

	return None

def handle_shard_create(config, author, channel, args):

	shard_type = parse_opts_shard_type(args)
	if not shard_type:
		return [{
			'title': 'Missing Shard Type',
			'description': 'You have to specify a shard type. It can be either:\n- `char` (for character arena),\n- or `ship` (for fleet arena).\n\nPlease type `%shelp shard` to get more help.' % config['prefix'],
		}]

	try:
		shard, created = Shard.objects.get(channel_id=channel.id), False

	except Shard.DoesNotExist:
		shard, created = Shard.objects.get_or_create(channel_id=channel.id, type=shard_type)

	if shard.type != shard_type:
		shard.type = shard_type
		shard.save()

	shard_type_str = Shard.SHARD_TYPES_DICT[shard_type].lower()

	return [{
		'title': 'Shard Created',
		'description': 'This channel is now dedicated to your shard for **%s**.\nNow you may add some members of your shard. Please type `%shelp shard` to learn how to add members to your shard.' % (shard_type_str, config['prefix']),
	}]

def handle_shard_add(config, author, channel, args):

	args, players, error = parse_opts_players(config, author, args)
	if error:
		return error

	if args:
		return error_unknown_parameters(args)

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return error_no_shard_found(config)

	ally_codes = [ x.ally_code for x in players ]

	new_members = []
	for ally_code in ally_codes:
		member, created = ShardMember.objects.get_or_create(shard=shard, ally_code=ally_code)
		if created:
			new_members.append(ally_code)

	plural = len(ally_codes) > 1 and 's' or ''
	plural_have = len(ally_codes) > 1 and 've' or 's'
	ally_code_str = '\n'.join([ '- **`%s`**' % x for x in new_members ])

	return [{
		'title': 'Shard Updated',
		'description': 'This shard has been updated.\nThe following ally code%s ha%s been **added**:\n%s' % (plural, plural_have, ally_code_str),
	}]

def handle_shard_del(config, author, channel, args):

	args, players, error = parse_opts_players(config, author, args)
	if error:
		return error

	if args:
		return error_unknown_parameters(args)

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return error_no_shard_found(config)

	ally_codes = [ x.ally_code for x in players ]

	ShardMember.objects.filter(shard=shard, ally_code__in=ally_codes).delete()

	plural = len(ally_codes) > 1 and 's' or ''
	plural_have = len(ally_codes) > 1 and 've' or 's'
	ally_code_str = '\n'.join([ '- **%s**' % x for x in ally_codes ])

	return [{
		'title': 'Shard Updated',
		'description': 'This shard has been updated.\nThe following ally code%s ha%s been **removed**:\n%s' % (plural, plural_have, ally_code_str),
	}]

def handle_shard_list(config, author, channel, args):

	if args:
		return error_unknown_parameters(args)

	try:
		player = Player.objects.get(discord_id=author.id)
		tzinfo = player.timezone

	except Player.DoesNotExist:
		player = None
		tzname = 'Europe/London'
		tzinfo = pytz.timezone(tzname)

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return error_no_shard_found(config)

	payout_times = get_payout_times(shard)
	ally_codes = list(payout_times)

	data = api_swgoh_players(config, {
		'allycodes': ally_codes,
		'project': {
			'name': 1,
			'allyCode': 1,
			'updated': 1,
			'arena': {
				'char': {
					'rank': 1,
				},
				'ship': {
					'rank': 1,
				},
			},
		},
	})

	lines = []
	players = sorted([ p for p in data ], key=lambda x: x['arena'][shard.type]['rank'])
	for p in players:
		bold = ''
		if player and player.ally_code == p['allyCode']:
			bold = '**'

		spacer = ''

		po_time = p['allyCode'] in payout_times and payout_times[ p['allyCode'] ]
		if po_time:
			now = datetime.now(pytz.utc)
			next_payout = datetime(year=now.year, month=now.month, day=now.day, hour=po_time.hour, minute=po_time.minute, second=0, microsecond=0, tzinfo=pytz.utc)
			if now > next_payout:
				next_payout += timedelta(hours=24)

			next_payout = next_payout.astimezone(tzinfo).strftime('%H:%M')

		else:
			next_payout = '??:??'

		updated = datetime.fromtimestamp(int(p['updated']) / 1000).strftime('%H:%M')
		lines.append('%s`| %s | %s | %s`%s' % (bold, next_payout, p['allyCode'], p['name'], bold))

	lines_str = '\n'.join(lines)

	return [{
		'title': 'Shard Status',
		'description': 'Shard payout time for **%s** arena:\n%s\n`| PO At | Ally Code | Name`\n%s\n%s' % (shard.type, config['separator'], config['separator'], lines_str),
	}]

def handle_shard_stats(config, author, channel, args):

	if args:
		return error_unknown_parameters(args)

	try:
		player = Player.objects.get(discord_id=author.id)
		tzinfo = player.timezone

	except Player.DoesNotExist:
		player = None
		tzname = 'Europe/London'
		tzinfo = pytz.timezone(tzname)

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return error_no_shard_found(config)

	payout_times = get_payout_times(shard)
	ally_codes = list(payout_times)

	data = api_swgoh_players(config, {
		'allycodes': ally_codes,
		'project': {
			'name': 1,
			'allyCode': 1,
			'updated': 1,
			'arena': {
				'char': {
					'rank': 1,
				},
				'ship': {
					'rank': 1,
				},
			},
		},
	})

	players_by_payout = {}
	players = sorted([ p for p in data ], key=lambda x: x['arena'][shard.type]['rank'])
	for p in players:

		po_time = p['allyCode'] in payout_times and payout_times[ p['allyCode'] ]
		if po_time not in players_by_payout:
			players_by_payout[po_time] = []

		players_by_payout[po_time].append(p)

	lines = []
	po_times = list(players_by_payout)
	po_times.reverse()
	for po_time in po_times:
		players = players_by_payout[po_time]
		for p in players:
			bold = ''
			if player and player.ally_code == p['allyCode']:
				bold = '**'

			spacer = ''
			rank = int(p['arena'][shard.type]['rank'])
			if rank < 10:
				spacer = '\u00a0' * 4
			elif rank < 100:
				spacer = '\u00a0' * 3
			elif rank < 1000:
				spacer = '\u00a0' * 2
			elif rank < 10000:
				spacer = '\u00a0' * 1

			po_time = p['allyCode'] in payout_times and payout_times[ p['allyCode'] ]
			if po_time:
				now = datetime.now(pytz.utc)
				next_payout = datetime(year=now.year, month=now.month, day=now.day, hour=po_time.hour, minute=po_time.minute, second=0, microsecond=0, tzinfo=pytz.utc)
				if now > next_payout:
					next_payout += timedelta(hours=24)

				seconds_before_payout = (next_payout - now).seconds
				hours, remain = divmod(seconds_before_payout, 3600)
				minutes, seconds = divmod(remain, 60)
				next_payout = '%02d:%02d' % (hours, minutes)

			else:
				next_payout = '??:??'

			updated = datetime.fromtimestamp(int(p['updated']) / 1000).strftime('%H:%M')
			lines.append('%s`|%s%s | %s | %s`%s' % (bold, spacer, rank, next_payout, p['name'], bold))

	lines_str = '\n'.join(lines)

	return [{
		'title': 'Shard Status',
		'description': 'Shard ranks and payouts for **%s** arena:\n%s\n`| Rank | PO At | Ally Code | Name`\n%s\n%s' % (shard.type, config['separator'], config['separator'], lines_str),
	}]

def handle_shard_export(config, author, channel, args):

	if args:
		return error_unknown_parameters(args)

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return error_no_shard_found(config)

	members = ShardMember.objects.filter(shard=shard)
	ally_codes = [ str(member.ally_code) for member in members ]
	if not ally_codes:
		return [{
			'title': 'Shard Export',
			'description': 'No player associated to this shard.',
		}]

	return [{
		'title': 'Shard Export',
		'description': '`%s`' % ' '.join(ally_codes)
	}]

def handle_shard_payout(config, author, channel, args):

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return error_no_shard_found(config)

	try:
		player = Player.objects.get(discord_id=author.id)
		tzname = player.timezone

	except Player.DoesNotExist:
		player = None
		tzname = 'Europe/London'

	args, players, error = parse_opts_players(config, author, args)
	if error:
		return error

	payout_time = parse_opts_payout_time(tzname, args)
	if not payout_time:
		return [{
			'title': 'Error: Missing payout time',
			'description': 'You have to supply a payout time in the following format: `HH:MM` (for example: `18:00`). Please type `%shelp shard` to get more help.',
		}]

	if args:
		return error_unknown_parameters(args)
		
	ally_codes = [ x.ally_code for x in players ]
	ShardMember.objects.filter(shard=shard, ally_code__in=ally_codes).update(payout_time=payout_time.strftime('%H:%M'))

	plural = len(ally_codes) > 1 and 's' or ''
	plural_have = len(ally_codes) > 1 and 've' or 's'
	ally_code_str = '\n'.join([ '- **%s**' % x for x in ally_codes ])

	return [{
		'title': 'Shard Payout Updated',
		'description': 'Payout time has been updated to **%s** for the following ally code%s:\n%s' % (payout_time.astimezone(tzname).strftime('%H:%M'), plural, ally_code_str),
	}]

shard_types = {
	'c':     'char',
	'char':  'char',
	'chars': 'char',
	's':     'ship',
	'ship':  'ship',
	'ships': 'ship',
}

subcommands = {
	'new':    handle_shard_create,
	'init':   handle_shard_create,
	'conf':   handle_shard_create,
	'config': handle_shard_create,
	'create': handle_shard_create,
	'set':    handle_shard_create,
	'add':    handle_shard_add,
	'del':    handle_shard_del,
	'delete': handle_shard_del,
	'rm':     handle_shard_del,
	'remove': handle_shard_del,
	'list':   handle_shard_list,
	'stat':   handle_shard_stats,
	'stats':  handle_shard_stats,
	'status': handle_shard_stats,
	'export': handle_shard_export,
	'payout': handle_shard_payout,
}

def parse_opts_subcommands(args):

	args_cpy = list(args)
	for arg in args_cpy:
		if arg.lower() in subcommands:
			args.remove(arg)
			return args, arg.lower()

	return args, None

def cmd_shard(config, author, channel, args):

	args, subcommand = parse_opts_subcommands(args)
	if not subcommand:
		subcommand = 'stats'

	if subcommand in subcommands:
		return subcommands[subcommand](config, author, channel, args)

	return error_generic('Unsupported Action', subcommand)
