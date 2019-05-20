#!/usr/bin/python3

from opts import *
from errors import *
from swgohhelp import api_swgoh_players

from swgoh.models import Player, Shard, ShardMember

from datetime import datetime

help_shard = {
	'title': 'Shard Help',
	'description': """Helps you tracking your shard ranks over time in arena.

**Syntax**
Adding members to your shard:
```
%prefixshard add [players]```
Removing members from your shard:
```
%prefixshard del [players]```
Showing char/ship arena rank for your shard members:
```
%prefixshard [char|ship]```
**Options**
- **`players`**: Can be a list of ally codes or discord mentions.
- **`char`** (or **`c`**): Show character arena rank (the default).
- **`ship`** (or **`s`**): Show fleet arena rank.

**Examples**
Add some members to your shard:
```
%prefixshard add 123456789 234567891 3456789012```
Or:
```
%prefixshard add 123-456-789 234-567-891 345-678-9012```
Remove some members from your shard:
```
%prefixshard del 123456789 234567891 3456789012```
List all players in your shard and their respective character arena rank:
```
%prefixshard char```
Or the short form:
```
%prefixshard c```
Or simply (because `char` is the default):
```
%prefixshard```
List all players in your shard and their respective fleet arena rank:
```
%prefixshard ship```
Or the short form:
```
%prefixshard s```"""
}

def handle_shard_add(config, author, args, shard_type):

	args, players, error = parse_opts_players(config, author, args)
	if error:
		return error

	try:
		player = Player.objects.get(discord_id=author.id)
		shard, created = Shard.objects.get_or_create(player=player, type='char')
		ally_codes = [ x.ally_code for x in players ]
		for ally_code in ally_codes:
			enemy, created = ShardMember.objects.get_or_create(shard=shard, ally_code=ally_code)

		shard_type_str = Shard.SHARD_TYPES_DICT[shard_type].lower()
		ally_code_str = '\n'.join([ '- **%s**' % x for x in ally_codes ])

		plural = len(ally_codes) > 1 and 's' or ''
		plural_have = len(ally_codes) > 1 and 've' or 's'
		return [{
			'title': 'Shard Updated',
			'description': '<@%s>\'s shard has been updated.\nThe following ally code%s ha%s been **added**:\n%s' % (author.id, plural, plural_have, ally_code_str),
		}]

	except Player.DoesNotExist:
		return error_no_ally_code_specified(config, author)

def handle_shard_del(config, author, args, shard_type):

	args, players, error = parse_opts_players(config, author, args)
	if error:
		return error

	try:
		player = Player.objects.get(discord_id=author.id)
		shard, created = Shard.objects.get_or_create(player=player, type='char')
		ally_codes = [ x.ally_code for x in players ]
		ShardMember.objects.filter(shard=shard, ally_code__in=ally_codes).delete()
		shard_type_str = Shard.SHARD_TYPES_DICT[shard_type].lower()
		ally_code_str = '\n'.join([ '- **%s**' % x for x in ally_codes ])

		plural = len(ally_codes) > 1 and 's' or ''
		plural_have = len(ally_codes) > 1 and 've' or 's'
		return [{
			'title': 'Shard Updated',
			'description': '<@%s>\'s shard for %s has been updated.\nThe following ally code%s ha%s been **removed**:\n%s' % (author.id, shard_type_str, plural, plural_have, ally_code_str),
		}]

	except Player.DoesNotExist:
		return error_no_ally_code_specified(config, author)

def handle_shard_stats(config, author, args, shard_type):

	try:
		player = Player.objects.get(discord_id=author.id)
		shard, created = Shard.objects.get_or_create(player=player, type='char')
		members = ShardMember.objects.filter(shard=shard)
		ally_codes = [ x.ally_code for x in members ]
		ally_codes.insert(0, player.ally_code)

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
			print('%s / %s' % (type(player.ally_code), type(p['allyCode'])))
			if player.ally_code == str(p['allyCode']):
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

			updated = datetime.fromtimestamp(int(p['updated']) / 1000).strftime('%H:%M')
			lines.append('%s`|%s%s | %s | %s`%s' % (bold, spacer, rank, p['allyCode'], p['name'], bold))

		lines_str = '\n'.join(lines)

		return [{
			'title': 'Shard Status',
			'description': 'Here is <@%s>\'s shard ranks for **%s** arena:\n%s\n`| Rank | Ally Code | Name`\n%s\n%s' % (author.id, shard_type, config['separator'], config['separator'], lines_str),
		}]

	except Player.DoesNotExist:
		return error_no_ally_code_specified(config, author)

	except Shard.DoesNotExist:
		return error_generic('Shard Not Found', 'I couldn\'t find the shard **%s** for <@%s>' % (shard_type, author.id))

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
}

def parse_opts_shard_type(args):

	args_cpy = list(args)
	for arg in args_cpy:
		if arg.lower() in shard_types:
			args.remove(arg)
			return args, shard_types[arg.lower()]

	return args, None

def parse_opts_subcommands(args):

	args_cpy = list(args)
	for arg in args_cpy:
		if arg.lower() in subcommands:
			args.remove(arg)
			return args, arg.lower()

	return args, None

def cmd_shard(config, author, channel, args):

	args, shard_type = parse_opts_shard_type(args)
	args, subcommand = parse_opts_subcommands(args)

	if not shard_type:
		shard_type = 'char'

	if not subcommand:
		subcommand = 'stats'

	if subcommand in subcommands:
		return subcommands[subcommand](config, author, args, shard_type)

	return error_generic('Unsupported Action', subcommand)
