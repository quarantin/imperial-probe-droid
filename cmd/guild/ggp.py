import json

from opts import *
from errors import *

from utils import get_star, translate
from swgohhelp import fetch_guilds

import DJANGO
from swgoh.models import BaseUnitSkill

help_guild_gp = {
	'title': 'Guild List Help',
	'description': """List your guild members matching some character requirements.

**Syntax**
```
%prefixglist [players] [filters]```
**Options**
Possible filters are:
**`gp<number>`**: To filter units by GP.
**`gear<number>`** or **`g<number>`**: To filter units by gear level.
**`level<number>`** or **`l<number>`**: To filter units by level.
**`star<number>`** or **`s<number>`** or **`<number>*`**: To filter units by rarity.

**Examples**
Search your guild for all player having Asajj Ventress at least Gear 12:
```
%prefixglist asajj g12```
Search your guild to see who's having Jedi Knight Revan with GP greater than 23000:
```
%prefixglist jkr gp23000```"""
}

def unit_is_matching(unit, char_filters):

	if unit['gp'] < char_filters['gp']:
		return False

	if unit['gear'] < char_filters['gear']:
		return False

	if unit['level'] < char_filters['level']:
		return False

	if unit['rarity'] < char_filters['rarity']:
		return False

	if BaseUnitSkill.get_relic(unit) < char_filters['relic']:
		return False

	return True

async def cmd_guild_gp(request):

	args = request.args
	author = request.author
	config = request.config

	language = parse_opts_lang(request)

	selected_char_filters = parse_opts_char_filters(request)

	selected_players, error = parse_opts_players(request)

	if error:
		return error

	if args:
		return error_unknown_parameters(args)

	if not selected_players:
		return error_no_ally_code_specified(config, author)

	fields = []
	ally_codes = [ p.ally_code for p in selected_players ]
	guild_list = await fetch_guilds(config, [ str(x) for x in ally_codes ])

	guilds = {}
	for target_ally_code, guild in guild_list.items():

		guild_name = guild['name']
		if guild_name not in guilds:
			guilds[guild_name] = {}

		for ally_code_str, player in guild['roster'].items():

			player_name = player['name']
			if player_name not in guilds[guild_name]:
				guilds[guild_name][player_name] = player

	lines = []
	lines.append('Name;AllyCode;GP;CharGP;ShipGP')
	for guild_name, guild in sorted(guilds.items()):
		for player_name in sorted(guild.keys(), key=str.casefold):
			player = guild[player_name]
			line = '%s;%s;%s;%s;%s' % (player_name, player['allyCode'], player['gp'], player['gpChar'], player['gpShip'])
			lines.append(line)

	content = '\n'.join(lines)

	return [{
		'title': 'Guild GP',
		'description': '```\n%s```' % content
	}]
