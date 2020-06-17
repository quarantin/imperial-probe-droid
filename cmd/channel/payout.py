from swgohgg import get_swgohgg_profile_url

import DJANGO
from swgoh.models import Player, Shard, ShardMember

import pytz
import inspect
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

def get_shard(ctx):

	alt = ctx.alt
	author = ctx.author
	channel = ctx.channel
	config = ctx.config

	if channel is None:
		return None

	try:
		return Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		pass

	try:
		player = Player.objects.get(discord_id=author.id, alt=alt)
		members = ShardMember.objects.filter(ally_code=player.ally_code)
		shards = []
		for member in members:
			if member.shard not in shards:
				shards.append(member.shard)

		for shard in shards:
			shard_channel = config['bot'].get_channel(shard.channel_id)
			if shard_channel:

				if channel.id == shard_channel.guild.id:
					return shard

				if hasattr(channel, 'guild') and channel.guild.id == shard_channel.guild.id:
					return shard

	except Player.DoesNotExist:
		pass

	return None

def handle_payout_create(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	channel = ctx.channel
	config = ctx.config

	if not bot.is_ipd_admin(author):
		return [{
			'title': 'Permission Denied',
			'color': 'red',
			'description': 'Only a member of the role **%s** can perform this operation.' % config['role'],
		}]

	shard_type = bot.options.parse_shard_type(args)
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

async def handle_payout_add(ctx):

	bot = ctx.bot
	args = ctx.args
	channel = ctx.channel
	config = ctx.config

	players, error = bot.options.parse_players(ctx, args)
	if error:
		return error

	if args:
		return bot.errors.unknown_parameters(args)

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return bot.errors.no_shard_found(ctx)

	ally_codes = [ x.ally_code for x in players ]
	invalid_ally_codes = []

	try:
		data = await bot.client.players(ally_codes=ally_codes)
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

def handle_payout_del(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	channel = ctx.channel
	config = ctx.config

	if not bot.is_ipd_admin(author):
		return [{
			'title': 'Permission Denied',
			'color': 'red',
			'description': 'Only a member of the role **%s** can perform this operation.' % config['role'],
		}]

	players, error = bot.options.parse_players(ctx, args)
	if error:
		return error

	if args:
		return bot.errors.unknown_parameters(args)

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return bot.errors.no_shard_found(ctx)

	ally_codes = [ x.ally_code for x in players ]

	ShardMember.objects.filter(shard=shard, ally_code__in=ally_codes).delete()

	plural = len(ally_codes) > 1 and 's' or ''
	plural_have = len(ally_codes) > 1 and 've' or 's'
	ally_code_str = '\n'.join([ '- **%s**' % x for x in ally_codes ])

	return [{
		'title': 'Shard Updated',
		'description': 'This shard has been updated.\nThe following ally code%s ha%s been **removed**:\n%s' % (plural, plural_have, ally_code_str),
	}]

async def handle_payout_rank(ctx):

	bot = ctx.bot
	alt = ctx.alt
	args = ctx.args
	author = ctx.author
	config = ctx.config

	if args:
		return bot.errors.unknown_parameters(args)

	try:
		player = Player.objects.get(discord_id=author.id, alt=alt)
		tzinfo = player.timezone

	except Player.DoesNotExist:
		player = None
		tzname = 'Europe/London'
		tzinfo = pytz.timezone(tzname)

	shard = get_shard(ctx)
	if not shard:
		return bot.errors.no_shard_found(ctx)

	payout_times = get_payout_times(shard)

	ally_codes = list(payout_times)
	data = await bot.client.players(ally_codes=ally_codes)

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

async def handle_payout_stats(ctx):

	bot = ctx.bot
	alt = ctx.alt
	args = ctx.args
	author = ctx.author
	channel = ctx.channel
	config = ctx.config
	from_user = ctx.from_user

	if args:
		return bot.errors.unknown_parameters(args)

	try:
		player = Player.objects.get(discord_id=author.id, alt=alt)
		tzinfo = player.timezone

	except Player.DoesNotExist:
		player = None
		tzname = 'Europe/London'
		tzinfo = pytz.timezone(tzname)

	shard = get_shard(ctx)
	if not shard:
		return bot.errors.no_shard_found(ctx)

	shard_channel = config['bot'].get_channel(shard.channel_id)
	payout_times = get_payout_times(shard)
	ally_codes = list(payout_times)

	data = await bot.client.players(ally_codes=ally_codes)

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
			profile_url = await get_swgohgg_profile_url(p['allyCode'], no_check=True)
			lines.append('%s`|%s%s %s` %s [%s](%s)%s' % (bold, spacer, rank, next_payout, affiliation, p['name'], profile_url, bold))

	lines_str = '\n'.join(lines)

	embeds = bot.embed.create({
		'title': 'Shard Status',
		'description': 'Shard ranks and payouts for **%s** arena:\n%s\n`|Rank PO_In 🔫 Player`\n%s\n%s' % (shard.type, config['separator'], config['separator'], lines_str),
	})

	try:
		if from_user is False and shard.message_id:
			message = await shard_channel.fetch_message(shard.message_id)
			await message.edit(embed=embeds[0])
			return []
	except:
		pass

	for embed in embeds:
		status, error = await config['bot'].sendmsg(channel, message='', embed=embed)
		if not status:
			if '403 FORBIDDEN' in str(error):
				Shard.objects.get(channel_id=shard.channel_id).delete()
				print('Could not print to channel %s: Deleting shard.' % channel)
			else:
				print('Could not print to channel %s: %s' % (channel, error))
		else:
			shard.message_id = error
			shard.save()

	return []

def handle_payout_export(ctx):

	bot = ctx.bot
	args = ctx.args
	channel = ctx.channel
	config = ctx.config

	if args:
		return bot.errors.unknown_parameters(args)

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return bot.errors.no_shard_found(ctx)

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

def handle_payout_time(ctx):

	bot = ctx.bot
	alt = ctx.alt
	args = ctx.args
	author = ctx.author
	channel = ctx.channel
	config = ctx.config

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return bot.errors.no_shard_found(ctx)

	try:
		player = Player.objects.get(discord_id=author.id, alt=alt)
		tzname = player.timezone

	except Player.DoesNotExist:
		player = None
		tzname = 'Europe/London'

	players, error = bot.options.parse_players(ctx, args)
	if error:
		return error

	payout_time = bot.options.parse_payout_time(tzname, args)
	if not payout_time:
		return [{
			'title': 'Missing payout time',
			'description': 'You have to supply a payout time in the following format: `HH:MM` (for example: `18:00`). Please type `%shelp payout` to get more help.',
		}]

	if args:
		return bot.errors.unknown_parameters(args)

	ally_codes = [ x.ally_code for x in players ]
	ShardMember.objects.filter(shard=shard, ally_code__in=ally_codes).update(payout_time=payout_time.strftime('%H:%M'))

	plural = len(ally_codes) > 1 and 's' or ''
	plural_have = len(ally_codes) > 1 and 've' or 's'
	ally_code_str = '\n'.join([ '- **%s**' % x for x in ally_codes ])

	return [{
		'title': 'Shard Payout Updated',
		'description': 'Payout time has been updated to **%s** for the following ally code%s:\n%s' % (payout_time.astimezone(tzname).strftime('%H:%M'), plural, ally_code_str),
	}]

def handle_payout_tag(ctx):

	bot = ctx.bot
	alt = ctx.alt
	args = ctx.args
	author = ctx.author
	channel = ctx.channel
	config = ctx.config

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return bot.errors.no_shard_found(ctx)

	try:
		player = Player.objects.get(discord_id=author.id, alt=alt)
		tzname = player.timezone

	except Player.DoesNotExist:
		player = None
		tzname = 'Europe/London'

	players, error = bot.options.parse_players(ctx, args)
	if error:
		return error

	affiliation_id, affiliation_display, affiliation_name = ShardMember.parse_affiliation(args)
	if affiliation_id is None:
		return [{
			'title': 'Missing Affiliation',
			'description': 'You have to supply an Affiliation. Valid affiliations are either: **`friendly`**, **`neutral`**, or **`enemy`**. Please type `%shelp payout` to get more help.',
		}]

	if args:
		return bot.errors.unknown_parameters(args)

	ally_codes = [ x.ally_code for x in players ]
	ShardMember.objects.filter(shard=shard, ally_code__in=ally_codes).update(affiliation=affiliation_id)

	plural = len(ally_codes) > 1 and 's' or ''
	plural_have = len(ally_codes) > 1 and 've' or 's'
	ally_code_str = '\n'.join([ '- **%s**' % x for x in ally_codes ])

	return [{
		'title': 'Affiliation Updated',
		'description': 'Affiliation has been changed to **`%s`** for the following ally code%s:\n%s' % (affiliation_name, plural, ally_code_str),
	}]

def handle_payout_destroy(ctx):

	bot = ctx.bot
	author = ctx.author
	channel = ctx.channel
	config = ctx.config

	if not bot.is_ipd_admin(author):
		return [{
			'title': 'Permission Denied',
			'color': 'red',
			'description': 'Only a member of the role **%s** can perform this operation.' % config['role'],
		}]

	try:
		shard = Shard.objects.get(channel_id=channel.id)

	except Shard.DoesNotExist:
		return bot.errors.no_shard_found(ctx)

	shard.delete()

	return [{
		'title': 'Deletion Successful',
		'description': 'This channel is not a shard channel anymore.'
	}]

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

def parse_opts_payout_subcommands(args, default='stats'):

	args_cpy = list(args)
	for arg in args_cpy:
		larg = arg.lower()
		if larg in subcommands:
			args.remove(arg)
			return larg

	return default

async def cmd_payout(ctx):

	bot = ctx.bot
	args = ctx.args

	ctx.alt = bot.options.parse_alt(args)
	subcommand = parse_opts_payout_subcommands(args)
	if not subcommand:
		subcommand = 'stats'

	if subcommand in subcommands:
		if inspect.iscoroutinefunction(subcommands[subcommand]):
			return await subcommands[subcommand](ctx)
		else:
			return subcommands[subcommand](ctx)

	return bot.errors.generic('Unsupported Action', subcommand)
