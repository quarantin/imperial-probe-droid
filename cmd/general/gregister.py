import DJANGO
from swgoh.models import Player

from errors import *
from opts import parse_opts_players
from swgohhelp import fetch_guilds

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
	return string and string.replace(' ', '').lower() or string

async def cmd_gregister(request):

	bot = request.bot
	args = request.args
	author = request.author
	config = request.config

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

	ally_codes = [ str(p.ally_code) for p in selected_players ]

	guilds = await fetch_guilds(config, ally_codes)

	for selector_allycode, guild in guilds.items():

		for allycode_str, player in guild['roster'].items():

			match = list(Player.objects.filter(ally_code=player['allyCode']))
			if match:
				registered.append('%s => @%s' % (player['name'], match[0]))
			else:
				nick = None
				member = None
				for m in request.server.members:

					member = m
					player_name = lowerstrip(player['name'])

					for attr in [ 'nick', 'display_name', 'name' ]:

						if hasattr(m, attr) and lowerstrip(getattr(m, attr)) == player_name:
							nick = getattr(m, attr)
							break

					if nick:
						break
				else:
					print("MISSING MEMBER: %s <=> %s" % (player['name'], nick))

				msg = '**Not Found** (%s)' % player['allyCode']
				if nick:
					auto_ids.append(member.id)
					auto_allycodes.append(player['allyCode'])
					msg = '%s *(auto)*' % nick
					if auto:
						registered.append('%s => @%s *(auto)*' % (player['name'], nick))

				if not auto or not nick:
					unregistered.append('%s => %s' % (player['name'], msg))

	if len(registered) == 1:
		registered.append('*No player registered yet.*')

	if len(unregistered) == 1:
		unregistered.append('*All players registered.*')

	lines = registered + [ '' ] + unregistered

	msgs = []
	if auto:
		msgs = await register_users(request, auto_ids, auto_allycodes)

	return msgs + [{
		'title': 'Who is Registered',
		'description': 'Add `auto` to automatically register missing members marked with *auto*.\n\n%s' % '\n'.join(lines),
	}]
