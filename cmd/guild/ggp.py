import json

from utils import get_star, translate

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

def compute_gp(player):

	total_gp = 0
	char_gp = 0
	ship_gp = 0

	for unit in player['roster']:

		gp = 'gp' in unit and unit['gp'] or 0

		total_gp += gp

		if unit['isShip']:
			ship_gp += gp

		else:
			char_gp += gp

	player['gp'] = total_gp
	player['gpChar'] = char_gp
	player['gpShip'] = ship_gp

async def cmd_guild_gp(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	config = ctx.config

	language = bot.options.parse_lang(ctx, args)

	selected_players, error = bot.options.parse_players(ctx, args)

	if error:
		return error

	if args:
		return bot.errors.unknown_parameters(args)

	if not selected_players:
		return bot.errors.no_ally_code_specified(ctx)

	fields = []
	ally_codes = [ x.ally_code for x in selected_players ]
	guilds = await bot.client.guilds(ally_codes=ally_codes, stats=True)
	if not guilds:
		return bot.errors.ally_codes_not_found(ally_codes)

	result = {}
	for selector, guild in guilds.items():

		guild_name = guild['name']
		if guild_name not in result:
			result[guild_name] = {}

		members = { x['id']: x for x in guild['members'] }
		for player_id, player in members.items():

			player_name = player['name']
			if player_name not in result[guild_name]:
				result[guild_name][player_name] = player

	lines = []
	lines.append('Name;AllyCode;GP;CharGP;ShipGP')
	for guild_name, guild in sorted(result.items()):
		for player_name in sorted(guild.keys(), key=str.casefold):
			player = guild[player_name]
			compute_gp(player)
			line = '%s;%s;%s;%s;%s' % (player_name, player['allyCode'], player['gp'], player['gpChar'], player['gpShip'])
			lines.append(line)

	content = '\n'.join(lines)

	return [{
		'title': 'Guild GP',
		'description': '```\n%s```' % content
	}]
