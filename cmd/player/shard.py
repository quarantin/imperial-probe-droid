from opts import *
from errors import *
from swgohhelp import api_swgoh_players

from swgoh.models import Player, Shard, ShardMember

from datetime import datetime

help_shard = {
	'title': 'Shard Help',
	'description': """Helps you to track the ranks of your shard members over time in character arena.

**Syntax**
Showing arena rank for your shard members:
```
%prefixshard```
Adding members to your shard:
```
%prefixshard add [players]```
Removing members from your shard:
```
%prefixshard del [players]```
Exporting ally codes from your shard:
```
%prefixshard export```
**Examples**
Add some members to your shard:
```
%prefixshard add 123456789 234567891 345-678-912```
Remove some members from your shard:
```
%prefixshard del 123-456-789 234567891 345678912```
List arena ranks of all members of your shard:
```
%prefixshard```
Export ally codes from your shard:
```
%prefixshard export```"""
}

help_fshard = {
	'title': 'Fshard Help',
	'description': """Helps you to track the ranks of your shard members over time in fleet arena.

**Syntax**
Adding members to your shard:
```
%prefixfshard add [players]```
Removing members from your shard:
```
%prefixfshard del [players]```
Showing arena rank for your shard members:
```
%prefixfshard```

**Examples**
Add some members to your shard:
```
%prefixfshard add 123456789 234567891 345-678-912```
Remove some members from your shard:
```
%prefixfshard del 123-456-789 234567891 345678912```
List arena ranks of all members of your shard:
```
%prefixfshard```"""
}

def handle_shard_add(config, author, args, shard_type):

	args, players, error = parse_opts_players(config, author, args)
	if error:
		return error

	if args:
		return error_unknown_parameters(args)

	try:
		player = Player.objects.get(discord_id=author.id)
		shard, created = Shard.objects.get_or_create(player=player, type=shard_type)
		ally_codes = [ x.ally_code for x in players ]

		# Add message author to his own shard
		if player.ally_code not in ally_codes:
			ally_codes.insert(0, player.ally_code)

		for ally_code in ally_codes:
			member, created = ShardMember.objects.get_or_create(shard=shard, ally_code=ally_code)

		shard_type_str = Shard.SHARD_TYPES_DICT[shard_type].lower()
		ally_code_str = '\n'.join([ '- **%s**' % x for x in ally_codes ])

		plural = len(ally_codes) > 1 and 's' or ''
		plural_have = len(ally_codes) > 1 and 've' or 's'
		return [{
			'title': 'Shard Updated',
			'description': '<@%s>\'s %s shard has been updated.\nThe following ally code%s ha%s been **added**:\n%s' % (author.id, shard_type_str, plural, plural_have, ally_code_str),
		}]

	except Player.DoesNotExist:
		return error_no_ally_code_specified(config, author)

def handle_shard_del(config, author, args, shard_type):

	args, players, error = parse_opts_players(config, author, args)
	if error:
		return error

	if args:
		return error_unknown_parameters(args)

	try:
		player = Player.objects.get(discord_id=author.id)
		shard, created = Shard.objects.get_or_create(player=player, type=shard_type)
		ally_codes = [ x.ally_code for x in players ]

		# Never remove the message author from his own shard
		if player.ally_code in ally_codes:
			ally_codes.remove(player.ally_code)

		ShardMember.objects.filter(shard=shard, ally_code__in=ally_codes).delete()
		shard_type_str = Shard.SHARD_TYPES_DICT[shard_type].lower()
		ally_code_str = '\n'.join([ '- **%s**' % x for x in ally_codes ])

		plural = len(ally_codes) > 1 and 's' or ''
		plural_have = len(ally_codes) > 1 and 've' or 's'
		return [{
			'title': 'Shard Updated',
			'description': '<@%s>\'s %s shard has been updated.\nThe following ally code%s ha%s been **removed**:\n%s' % (author.id, shard_type_str, plural, plural_have, ally_code_str),
		}]

	except Player.DoesNotExist:
		return error_no_ally_code_specified(config, author)

def get_payout_times(shard):

	res = {}
	members = ShardMember.objects.filter(shard=shard)
	for member in members:
		res[member.ally_code] = member.payout_time

	return res

def handle_shard_stats(config, author, args, shard_type):

	if args:
		return error_unknown_parameters(args)

	try:
		player = Player.objects.get(discord_id=author.id)
		shard, created = Shard.objects.get_or_create(player=player, type=shard_type)
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
		players = sorted([ p for p in data ], key=lambda x: x['arena'][shard_type]['rank'])
		for p in players:
			bold = ''
			if player.ally_code == p['allyCode']:
				bold = '**'

			spacer = ''
			rank = int(p['arena'][shard_type]['rank'])
			if rank < 10:
				spacer = '\u00a0' * 4
			elif rank < 100:
				spacer = '\u00a0' * 3
			elif rank < 1000:
				spacer = '\u00a0' * 2
			elif rank < 10000:
				spacer = '\u00a0' * 1

			payout_time = p['allyCode'] in payout_times and payout_times[ p['allyCode'] ] or '??:??'

			updated = datetime.fromtimestamp(int(p['updated']) / 1000).strftime('%H:%M')
			lines.append('%s`|%s%s | %s | %s | %s`%s' % (bold, spacer, rank, payout_time, p['allyCode'], p['name'], bold))

		lines_str = '\n'.join(lines)

		return [{
			'title': 'Shard Status',
			'description': 'Here is <@%s>\'s shard ranks for **%s** arena:\n%s\n`| Rank | PO At | Ally Code | Name`\n%s\n%s' % (author.id, shard_type, config['separator'], config['separator'], lines_str),
		}]

	except Player.DoesNotExist:
		return error_no_ally_code_specified(config, author)

def handle_shard_export(config, author, args, shard_type):

	if args:
		return error_unknown_parameters(args)

	try:
		player = Player.objects.get(discord_id=author.id)
		shard, created = Shard.objects.get_or_create(player=player, type=shard_type)
		members = ShardMember.objects.filter(shard=shard)
		ally_codes = []
		for member in members:
			ally_codes.append(str(member.ally_code))

		return [{
			'title': 'Shard Export',
			'description': 'Here is <@%s>\'s shard export for **%s** arena:\n%s\n`%s`' % (author.id, shard_type, config['separator'], ' '.join(ally_codes))
		}]

	except Player.DoesNotExist:
		return error_no_ally_code_specified(config, author)

def parse_opts_payout_time(args):

	import re

	args_cpy = list(args)

	for arg in args_cpy:
		result = re.match('^[0-9][0-9]:[0-9][0-9]$', arg)
		if result:
			args.remove(arg)
			return result[0]

	return None

def handle_shard_payout(config, author, args, shard_type):

	args, players, error = parse_opts_players(config, author, args)
	if error:
		return error

	payout_time = parse_opts_payout_time(args)
	if not payout_time:
		return [{
			'title': 'Error: Missing payout time',
			'description': 'You have to supply payout time. TODO',
		}]

	if args:
		return error_unknown_parameters(args)

	try:
		player = Player.objects.get(discord_id=author.id)
		shard, created = Shard.objects.get_or_create(player=player, type=shard_type)
		ally_codes = [ x.ally_code for x in players ]
		ShardMember.objects.filter(shard=shard, ally_code__in=ally_codes).update(payout_time=payout_time)
		shard_type_str = Shard.SHARD_TYPES_DICT[shard_type].lower()
		ally_code_str = '\n'.join([ '- **%s**' % x for x in ally_codes ])

		plural = len(ally_codes) > 1 and 's' or ''
		plural_have = len(ally_codes) > 1 and 've' or 's'
		return [{
			'title': 'Shard Payout Updated',
			'description': '<@%s>\'s %s shard payout has been updated to **%s** for the following ally code%s:\n%s' % (author.id, shard_type_str, payout_time, plural, ally_code_str),
		}]

	except Player.DoesNotExist:
		return error_no_ally_code_specified(config, author)

shard_types = {
	'c':     'char',
	'char':  'char',
	'chars': 'char',
	's':     'ship',
	'ship':  'ship',
	'ships': 'ship',
}

subcommands = {
	'add':    handle_shard_add,
	'del':    handle_shard_del,
	'delete': handle_shard_del,
	'rm':     handle_shard_del,
	'remove': handle_shard_del,
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

def _cmd_shard(config, author, channel, args, shard_type):

	args, subcommand = parse_opts_subcommands(args)
	if not subcommand:
		subcommand = 'stats'

	if subcommand in subcommands:
		return subcommands[subcommand](config, author, args, shard_type)

	return error_generic('Unsupported Action', subcommand)

def cmd_shard(config, author, channel, args):
	return _cmd_shard(config, author, channel, args, 'char')

def cmd_fshard(config, author, channel, args):
	return _cmd_shard(config, author, channel, args, 'ship')
