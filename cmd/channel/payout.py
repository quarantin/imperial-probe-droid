# -*- coding=utf-8 -*-

from opts import *
from errors import *
from swgohgg import get_swgohgg_profile_url
from swgohhelp import api_swgoh_players

import DJANGO
from swgoh.models import Player, Shard, ShardMember

import pytz
from datetime import datetime, timedelta

help_payout = {
	'title': 'Payout Help',
	'description': """Helps you to track payout time and arena rank of your shard members over time.

**Syntax**
Creating a shard channel for character arena:
```
%prefixpayout create char```
Creating a shard channel for fleet arena:
```
%prefixpayout create ship```
Adding members to your shard:
```
%prefixpayout add [players]```
Removing members from your shard:
```
%prefixpayout del [players]```
Setting payout time for some of your shard members:
```
%prefixpayout time HH:MM [players]```
Show members from your shard with their payout time sorted by rank:
```
%prefixpayout rank```
Set affiliation of your shard members (friendly, neutral, enemy):
```
%prefixpayout tag [friendly|neutral|enenmy] [players]```
Show members from your shard with their rank sorted by time left to payout:
```
%prefixpayout```
Exporting ally codes from your shard:
```
%prefixpayout export```
Destroy the shard in case you don't want to use it anymore:
(WARNING: THIS CANNOT BE UNDONE, ALL DATA WILL BE LOST)
```
%prefixpayout destroy```
**Aliases**
```
%prefixpo```
**Examples**
Create a channel for your character arena shard:
```
%prefixpayout create char```
Add some members to your shard:
```
%prefixpayout add 123456789 234567891 345-678-912```
Remove some members from your shard:
```
%prefixpayout del 123-456-789 234567891 345678912```
List arena ranks of all members of your shard:
```
%prefixpayout```
Set payout time for two of your shard members:
```
%prefixpayout time 18:00 123456789 234567891```
Export ally codes from your shard:
```
%prefixpayout export```"""
}

def get_payout_times(shard):

	res = {}
	members = ShardMember.objects.filter(shard=shard)
	for member in members:
		res[member.ally_code] = member

	return res

def get_shard(config, channel, author):

	try:
		return Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		pass

	try:
		player = Player.objects.get(discord_id=author.id)
		members = ShardMember.objects.filter(ally_code=player.ally_code)
		shards = []
		for member in members:
			if member.shard not in shards:
				shards.append(member.shard)

		for shard in shards:
			shard_channel = config['bot'].get_channel(shard.channel_id)
			if shard_channel and shard_channel.guild.id == channel.guild.id:
				return shard

	except Player.DoesNotExist:
		pass

	return None

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
		result = re.match('^[0-9]{1,2}[:h][0-9]{1,2}$', arg)
		if result:
			args.remove(arg)
			now = datetime.now(tz)
			tokens = result[0].replace('h', ':').split(':')
			return now.replace(hour=int(tokens[0]), minute=int(tokens[1]), second=0, microsecond=0).astimezone(pytz.utc)

	return None

DEFAULT_ROLE = 'IPD Admin'

def check_permission(config, author):

	if 'role' not in config:
		config['role'] = DEFAULT_ROLE

	ipd_role = config['role'].lower()
	for role in author.roles:
		if role.name.lower() == ipd_role:
			return True

	return False

def handle_payout_create(config, author, channel, args):

	if not check_permission(config, author):
		return [{
			'title': 'Permssion Denied',
			'color': 'red',
			'description': 'Only a member of the role **%s** can perform this operation.' % config['role'],
		}]

	shard_type = parse_opts_shard_type(args)
	if not shard_type:
		return [{
			'title': 'Missing Shard Type',
			'description': 'You have to specify a shard type. It can be either:\n- `char` (for character arena),\n- or `ship` (for fleet arena).\n\nPlease type `%shelp payout` to get more help.' % config['prefix'],
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
		'description': 'This channel is now dedicated to your shard for **%s**.\nNow you may add some members of your shard. Please type `%shelp payout` to learn how to add members to your shard.' % (shard_type_str, config['prefix']),
	}]

def handle_payout_add(config, author, channel, args):

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
	invalid_ally_codes = []

	try:
		data = api_swgoh_players(config, {
			'allycodes': ally_codes,
			'project': {
				'name': 1,
				'allyCode': 1,
			},
		}, force=False)

		data = { x['allyCode']: x for x in data }
		for ally_code in ally_codes:
			if ally_code not in data:
				print('Missing ally code from result: %s' % ally_code)
				invalid_ally_codes.append(str(ally_code))

	except Exception as err:
		errmsg = 'Could not find any players affiliated with these allycodes'
		if errmsg in str(err):
			invalid_ally_codes = [ str(x) for x in ally_codes ]

	if invalid_ally_codes:
		verb = len(invalid_ally_codes) > 1 and 'are' or 'is'
		plural = len(invalid_ally_codes) > 1 and 's' or ''
		return [{
			'title': 'Invalid Ally Code%s' % plural,
			'description': 'The following ally code%s %s **invalid**:\n- %s' % (plural, verb, '\n- '.join(invalid_ally_codes)),
			'color': 'red',
		}]

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

def handle_payout_del(config, author, channel, args):

	if not check_permission(config, author):
		return [{
			'title': 'Permssion Denied',
			'color': 'red',
			'description': 'Only a member of the role **%s** can perform this operation.' % config['role'],
		}]

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

def handle_payout_rank(config, author, channel, args):

	if args:
		return error_unknown_parameters(args)

	try:
		player = Player.objects.get(discord_id=author.id)
		tzinfo = player.timezone

	except Player.DoesNotExist:
		player = None
		tzname = 'Europe/London'
		tzinfo = pytz.timezone(tzname)

	shard = get_shard(config, channel, author)
	if not shard:
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
		rank = int(p['arena'][shard.type]['rank'])
		if rank < 10:
			spacer = '\u00a0' * 3
		elif rank < 100:
			spacer = '\u00a0' * 2
		elif rank < 1000:
			spacer = '\u00a0' * 1

		po_time = p['allyCode'] in payout_times and payout_times[ p['allyCode'] ].payout_time
		if po_time:
			now = datetime.now(pytz.utc)
			next_payout = datetime(year=now.year, month=now.month, day=now.day, hour=po_time.hour, minute=po_time.minute, second=0, microsecond=0, tzinfo=pytz.utc)
			if now > next_payout:
				next_payout += timedelta(hours=24)

			next_payout = next_payout.astimezone(tzinfo).strftime('%H:%M')

		else:
			next_payout = '--:--'

		#updated = datetime.fromtimestamp(int(p['updated']) / 1000).strftime('%H:%M')
		lines.append('%s`|%s%s %s %s %s`%s' % (bold, spacer, rank, next_payout, p['allyCode'], p['name'], bold))

	lines_str = '\n'.join(lines)

	return [{
		'title': 'Shard Ranks',
		'description': 'Shard payout time for **%s** arena:\n%s\n`|Rank PO_At Ally_Code Name`\n%s\n%s' % (shard.type, config['separator'], config['separator'], lines_str),
	}]

def handle_payout_stats(config, author, channel, args):

	if args:
		return error_unknown_parameters(args)

	try:
		player = Player.objects.get(discord_id=author.id)
		tzinfo = player.timezone

	except Player.DoesNotExist:
		player = None
		tzname = 'Europe/London'
		tzinfo = pytz.timezone(tzname)

	shard = get_shard(config, channel, author)
	if not shard:
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

	now = datetime.now(pytz.utc)

	players_by_payout = {}
	players = sorted([ p for p in data ], key=lambda x: x['arena'][shard.type]['rank'])
	for p in players:

		diff = None
		member = p['allyCode'] in payout_times and payout_times[ p['allyCode'] ]
		if member:
			po_time = member.payout_time
			if po_time:
				po_time = now.replace(hour=po_time.hour, minute=po_time.minute, second=po_time.second)
				if po_time < now:
					po_time += timedelta(hours=24)

				diff = (po_time - now).total_seconds()

		if diff not in players_by_payout:
			players_by_payout[diff] = []

		players_by_payout[diff].append(p)

	lines = []
	po_times = list(players_by_payout)
	none_entry = False
	if None in po_times:
		none_entry = True
		po_times.remove(None)
	po_times.sort()
	if none_entry:
		po_times.append(None)
	for diff_time in po_times:
		players = players_by_payout[diff_time]
		for p in players:
			bold = ''
			if player and player.ally_code == p['allyCode']:
				bold = '**'

			spacer = ''
			rank = int(p['arena'][shard.type]['rank'])
			if rank < 10:
				spacer = '\u00a0' * 3
			elif rank < 100:
				spacer = '\u00a0' * 2
			elif rank < 1000:
				spacer = '\u00a0' * 1

			if diff_time:
				hours, remain = divmod(diff_time, 3600)
				minutes, seconds = divmod(remain, 60)
				next_payout = '%02d:%02d' % (hours, minutes + 1)

			else:
				next_payout = '--:--'
			#updated = datetime.fromtimestamp(int(p['updated']) / 1000).strftime('%H:%M')
			affiliation = p['allyCode'] in payout_times and payout_times[ p['allyCode'] ].get_affiliation_display()
			profile_url = get_swgohgg_profile_url(p['allyCode'], no_check=True)
			lines.append('%s`|%s%s %s %s ` [%s](%s)%s' % (bold, spacer, rank, next_payout, affiliation, p['name'], profile_url, bold))

	lines_str = '\n'.join(lines)

	return [{
		'title': 'Shard Status',
		'description': 'Shard ranks and payouts for **%s** arena:\n%s\n`|Rank PO_In 🔫 Player`\n%s\n%s' % (shard.type, config['separator'], config['separator'], lines_str),
	}]

def handle_payout_export(config, author, channel, args):

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

def handle_payout_time(config, author, channel, args):

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
			'description': 'You have to supply a payout time in the following format: `HH:MM` (for example: `18:00`). Please type `%shelp payout` to get more help.',
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

def handle_payout_tag(config, author, channel, args):

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

	affiliation_id, affiliation_display, affiliation_name = ShardMember.parse_affiliation(args)
	if affiliation_id is None:
		return [{
			'title': 'Error: Missing Affiliation',
			'description': 'You have to supply an Affiliation. Valid affiliations are either: **`friendly`**, **`neutral`**, or **`enemy`**. Please type `%shelp payout` to get more help.',
		}]

	if args:
		return error_unknown_parameters(args)

	ally_codes = [ x.ally_code for x in players ]
	ShardMember.objects.filter(shard=shard, ally_code__in=ally_codes).update(affiliation=affiliation_id)

	plural = len(ally_codes) > 1 and 's' or ''
	plural_have = len(ally_codes) > 1 and 've' or 's'
	ally_code_str = '\n'.join([ '- **%s**' % x for x in ally_codes ])

	return [{
		'title': 'Affiliation Updated',
		'description': 'Affiliation has been changed to **`%s`** for the following ally code%s:\n%s' % (affiliation_name, plural, ally_code_str),
	}]

def handle_payout_destroy(config, author, channel, args):

	if not check_permission(config, author):
		return [{
			'title': 'Permssion Denied',
			'color': 'red',
			'description': 'Only a member of the role **%s** can perform this operation.' % config['role'],
		}]

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return error_no_shard_found(config)

	shard.delete()

	return [{
		'title': 'Deletion Successful',
		'description': 'This channel is not a shard channel anymore.'
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
	'new':     handle_payout_create,
	'init':    handle_payout_create,
	'conf':    handle_payout_create,
	'config':  handle_payout_create,
	'create':  handle_payout_create,
	'set':     handle_payout_create,
	'add':     handle_payout_add,
	'del':     handle_payout_del,
	'delete':  handle_payout_del,
	'rm':      handle_payout_del,
	'remove':  handle_payout_del,
	'list':    handle_payout_rank,
	'rank':    handle_payout_rank,
	'ranks':   handle_payout_rank,
	'stat':    handle_payout_stats,
	'stats':   handle_payout_stats,
	'status':  handle_payout_stats,
	'export':  handle_payout_export,
	'time':    handle_payout_time,
	'tag':     handle_payout_tag,
	'destroy': handle_payout_destroy,
}

def parse_opts_subcommands(args):

	args_cpy = list(args)
	for arg in args_cpy:
		if arg.lower() in subcommands:
			args.remove(arg)
			return args, arg.lower()

	return args, None

def cmd_payout(config, author, channel, args):

	args, subcommand = parse_opts_subcommands(args)
	if not subcommand:
		subcommand = 'stats'

	if subcommand in subcommands:
		return subcommands[subcommand](config, author, channel, args)

	return error_generic('Unsupported Action', subcommand)
