import DJANGO
from swgoh.models import Player

from utils import get_fuzz_ratio

from cmd.general.register import register_users

help_gregister = {
	'title': 'Whois Registered Help',
	'description': """Show who in your guild is registered to the bot.
	
**Syntax**
```
%prefixgregister [players]```
**Aliases**
```
%prefixgreg
%prefixgr```"""
}

def lowerstrip(string):

	if not string:
		return ''

	replaceable = {
		' ': '',
		'-': '',
		'_': '',
	}

	string = string.lower()
	for pattern, replace in replaceable.items():
		string = string.replace(pattern, replace)

	return string

async def cmd_gregister(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	config = ctx.config

	min_length = 4
	min_fuzz_ratio = 90

	auto = bot.options.parse_auto(args)
	ctx.alt = bot.options.parse_alt(args)
	selected_players, error = bot.options.parse_players(ctx, args)

	if error:
		return error

	if args:
		return bot.errors.unknown_parameters(args)

	if not selected_players:
		return bot.errors.no_ally_code_specified(ctx)

	if not hasattr(ctx.channel, 'guild') or not ctx.channel.guild:
		return bot.errors.invalid_guild_channel(ctx)

	auto_ids = []
	auto_allycodes = []
	registered = [ '**Registered Players**' ]
	unregistered = [ '**Unregistered Players**' ]

	ally_codes = [ x.ally_code for x in selected_players ]
	guilds = await bot.client.guilds(ally_codes=ally_codes, full=True)

	for player in selected_players:

		selector = player.ally_code
		guild = guilds[selector]
		guild_roster = { x['id']: x for x in guild['members'] }

		for player_id, player in guild_roster.items():

			player_name = lowerstrip(player['name'])
			match = list(Player.objects.filter(ally_code=player['allyCode']))
			if match:
				registered.append('%s => <@%s>' % (player['name'], match[0].discord_id))

			else:
				nick = None
				member = None
				for m in ctx.channel.guild.members:

					member = m

					for attr in [ 'nick', 'display_name', 'name' ]:

						member_name = hasattr(member, attr) and lowerstrip(getattr(member, attr)) or ''
						if not member_name:
							continue

						if len(member_name) >= min_length and len(player_name) >= min_length and (member_name in player_name or player_name in member_name):
							nick = getattr(member, attr)
							break

						fuzz_ratio = get_fuzz_ratio(player_name, member_name)
						if fuzz_ratio >= min_fuzz_ratio:
							nick = getattr(member, attr)
							break

					if nick:
						break
				else:
					print("MISSING MEMBER: %s <=> %s" % (player['name'], nick))

				msg = '%s => **Not Found** (%s)' % (player['name'], player['allyCode'])
				if nick:
					auto_ids.append(member.id)
					auto_allycodes.append(player['allyCode'])
					msg = '%s => <@%s> *(auto)*' % (player['name'], member.id)
					if auto:
						registered.append(msg)

				if not auto or not nick:
					unregistered.append(msg)

	if len(registered) == 1:
		registered.append('*No player registered yet.*')

	if len(unregistered) == 1:
		unregistered.append('*All players registered.*')

	lines = sorted(registered, key=str.casefold) + [ '' ] + sorted(unregistered, key=str.casefold)

	msgs = []
	if auto:
		msgs = await register_users(ctx, auto_ids, auto_allycodes)

	return msgs + [{
		'title': 'Who is Registered',
		'description': 'Add `auto` to automatically register missing members marked with *auto*.\n\n%s' % '\n'.join(lines),
	}]
