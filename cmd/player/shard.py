#!/usr/bin/python3

from opts import *
from errors import *
from swgohhelp import api_swgoh_players

from swgoh.models import Player, Shard, ShardMember

from datetime import datetime

help_shard = {
	'title': 'Shard Help',
	'description': """Helps you to track your shard progress over time in arena.

**Syntax**
```
%prefixshard [add|del|stat] [players]```
**Examples**
List all players in your shard:
```
%prefixshard```
Add some players to your shard:
```
%prefixshard add 123456789 234567891 3456789012```
Remove some players from your shard:
```
%prefixshard del 123456789 234567891 3456789012```
Show character and fleet arena status of your shard:
```
%prefixshard stat```"""
}

def parse_opts_shard_type(args):

	args_cpy = list(args)
	for arg in args_cpy:
		if arg.lower() in [ 'char', 'ship' ]:
			args.remove(arg)
			return args, arg.lower()

	return args, None

def handle_new_shard(config, author, args, shard_type):

	try:
		player = Player.objects.get(discord_id=author.id)
		shard, created = Shard.objects.get_or_create(player=player, type=shard_type)
		if not created:
			return error_generic('Duplicate Shard', '<@%s> already has a shard for %s' % (author.id, shard_type.lower()))

		shard_type_string = Shard.SHARD_TYPES_DICT[shard_type].lower()

		return [{
			'title': 'New Shard Created',
			'description': 'A new shard was created by <@%s> for %s.' % (author.id, shard_type_string),
		}]

	except Player.DoesNotExist:
		return error_no_ally_code_specified(config, author)

def handle_list_shard(config, author, args, shard_type):

	try:
		player = Player.objects.get(discord_id=author.id)

	except Player.DoesNotExist:
		return error_no_ally_code_specified(config, author)

	if shard_type:
		shard, created = Shard.objects.get_or_create(player=player, type=shard_type)
		members = ShardMember.objects.filter(shard=shard)

		members_str = '\n'.join([ '- %s' % e.ally_code for e in members ])
		if members_str:
			members_str = 'Here is <@%s>\'s shard members:\n%s' % (author.id, members_str)
		else:
			members_str = 'No members defined in your shard yet.'

		return [{
			'title': 'List of Shard Members',
			'description': members_str,
		}]

	else:
		shards = [ x for x in Shard.objects.filter(player=player) ]
		if not shards:
			return [{
				'title': 'No Shard Defined',
				'description': 'You haven\'t created any shard yet. Please use `%sshard new char` or `%sshard new ship` to create a shard. See `%shelp shard` for more information.' % (config['prefix'], config['prefix'], config['prefix']),
			}]

		shards = [ '- **%s**' % x.type for x in shards ]

		return [{
			'title': 'List of Shards',
			'description': 'Here is <@%s>\'s shards:\n%s' % (author.id, '\n'.join(shards)),
		}]

def handle_add_player(config, author, args, shard_type):

	args, players, error = parse_opts_players(config, author, args)
	if error:
		return error

	try:
		player = Player.objects.get(discord_id=author.id)
		shard, created = Shard.objects.get_or_create(player=player, type=shard_type)
		ally_codes = [ x.ally_code for x in players ]
		for ally_code in ally_codes:
			enemy, created = ShardMember.objects.get_or_create(shard=shard, ally_code=ally_code)

		shard_type_str = Shard.SHARD_TYPES_DICT[shard_type].lower()
		ally_code_str = '\n'.join([ '- **%s**' % x for x in ally_codes ])

		plural = len(ally_codes) > 1 and 's' or ''
		plural_have = len(ally_codes) > 1 and 've' or 's'
		return [{
			'title': 'Shard Updated',
			'description': '<@%s>\'s shard for %s has been updated.\nThe following ally code%s ha%s been **added**:\n%s' % (author.id, shard_type_str, plural, plural_have, ally_code_str),
		}]

	except Player.DoesNotExist:
		return error_no_ally_code_specified(config, author)

def handle_del_player(config, author, args, shard_type):

	args, players, error = parse_opts_players(config, author, args)
	if error:
		return error

	try:
		player = Player.objects.get(discord_id=author.id)
		shard, created = Shard.objects.get_or_create(player=player, type=shard_type)
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
		shard, created = Shard.objects.get_or_create(player=player, type=shard_type)
		members = ShardMember.objects.filter(shard=shard)
		ally_codes = [ x.ally_code for x in members]
		ally_codes.insert(0, player.ally_code)

		data = api_swgoh_players(config, {
			'allycodes': ally_codes,
			'project': {
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
		for player in data:
			updated = datetime.fromtimestamp(int(player['updated']) / 1000).strftime('%m-%d %H:%M:%S')
			lines.append('`%s | %s | `**%s**` | `**%s**' % (player['allyCode'], updated, player['arena']['char']['rank'], player['arena']['ship']['rank']))

		lines_str = '\n'.join(lines)

		return [{
			'title': 'Shard Status',
			'description': 'Here is <@%s>\'s shard status:\n%s\n`Ally Code | Updated | Char | Ship`\n%s' % (author.id, config['separator'], lines_str),
		}]

	except Player.DoesNotExist:
		return error_no_ally_code_specified(config, author)

	except Shard.DoesNotExist:
		return error_generic('Shard Not Found', 'I couldn\'t find the shard **%s** for <@%s>' % (shard_type, author.id))

subcommands = {
	'add':    handle_add_player,
	'del':    handle_del_player,
	'delete': handle_del_player,
	'rm':     handle_del_player,
	'remove': handle_del_player,
	'list':   handle_list_shard,
	'stat':   handle_shard_stats,
	'stats':  handle_shard_stats,
	'status': handle_shard_stats,
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
	args, shard_type = parse_opts_shard_type(args)

	if not subcommand:
		subcommand = 'list'

	if not shard_type:
		shard_type = 'char'

	if subcommand in subcommands:
		return subcommands[subcommand](config, author, args, shard_type)

	return error_generic('Unsupported Action', subcommand)
