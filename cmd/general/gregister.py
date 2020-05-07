import DJANGO
from swgoh.models import Player

from errors import *
from utils import get_fuzz_ratio
from opts import parse_opts_players

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

def parse_opts_auto(request):

	args = request.args
	args_cpy = list(args)
	for arg in args_cpy:
		if arg.lower() == 'auto':
			args.remove(arg)
			return True

	return False

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

async def cmd_gregister(request):

	bot = request.bot
	args = request.args
	author = request.author
	config = request.config

	min_length = 4
	min_fuzz_ratio = 90

	auto = parse_opts_auto(request)

	selected_players, error = parse_opts_players(request)
	if error:
		return error

	if args:
		return error_unknown_parameters(args)

	auto_ids = []
	auto_allycodes = []
	registered = [ '**Registered Players**' ]
	unregistered = [ '**Unregistered Players**' ]

	ally_codes = [ x.ally_code for x in selected_players ]
	guilds = await bot.client.guilds(ally_codes=ally_codes, full=True)

	for player in selected_players:

		selector = player.ally_code
		guild = guilds[selector]
		guild_roster = { x['playerId']: x for x in guild['roster'] }

		for player_id, player in guild_roster.items():

			player_name = lowerstrip(player['name'])
			match = list(Player.objects.filter(ally_code=player['allyCode']))
			if match:
				registered.append('%s => <@%s>' % (player['name'], match[0].discord_id))

			else:
				nick = None
				member = None
				for m in request.server.members:

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
		msgs = await register_users(request, auto_ids, auto_allycodes)

	return msgs + [{
		'title': 'Who is Registered',
		'description': 'Add `auto` to automatically register missing members marked with *auto*.\n\n%s' % '\n'.join(lines),
	}]
