from opts import *
from errors import *

from utils import get_relic_tier, get_star, translate
from swgohhelp import sort_players, fetch_crinolo_stats, fetch_guilds

help_guild_list = {
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

	if get_relic_tier(unit) < char_filters['relic']:
		return False

	return True

async def cmd_guild_list(request):

	args = request.args
	author = request.author
	config = request.config

	language = parse_opts_lang(request)

	selected_char_filters = parse_opts_char_filters(request)

	selected_players, error = parse_opts_players(request)

	selected_units = parse_opts_unit_names(request)

	if error:
		return error

	if args:
		return error_unknown_parameters(args)

	if not selected_players:
		return error_no_ally_code_specified(config, author)

	if not selected_units:
		return error_no_unit_selected()

	fields = []
	ally_codes = [ p.ally_code for p in selected_players ]
	guild_list = await fetch_guilds(config, [ str(x) for x in ally_codes ])

	for root_ally_code, guild in guild_list.items():
		for ally_code, player in guild['roster'].items():
			if int(player['allyCode']) not in ally_codes:
				ally_codes.append(int(player['allyCode']))

	images = {}
	matches = {}
	stats, players = await fetch_crinolo_stats(config, ally_codes, units=selected_units)

	players = sort_players(players)

	for ally_code, player in players.items():
		if 'guildName' not in player:
			config['bot'].logger.info('Ignoring player with no guild: %s' % ally_code)
			continue

		guild_name = player['guildName']
		player_name = player['name']
		for ref_unit in selected_units:

			if guild_name not in matches:
				matches[guild_name] = {}

			if player_name not in matches[guild_name]:
				matches[guild_name][player_name] = {}

			base_id = ref_unit.base_id
			if base_id not in player['roster']:
				#print('Unit is locked for: %s' % player_name)
				continue

			unit = stats[ally_code][base_id]
			if not unit_is_matching(unit, selected_char_filters):
				#print('Unit does not match criteria for: %s' % player_name)
				continue

			images[ref_unit.name] = ref_unit.get_image()
			translated_unit_name = translate(ref_unit.base_id, language)
			matches[guild_name][player_name][ref_unit.name] = {
				'gp':      unit['gp'],
				'gear':    unit['gear'],
				'level':   unit['level'],
				'rarity':  unit['rarity'],
				'relic':   get_relic_tier(unit),
				'base_id': ref_unit.base_id,
				'name':    translated_unit_name,
				'url':     ref_unit.get_url(),
			}

	meta = {}
	units = {}

	for guild_name, players in matches.items():
		for player_name, unit_names in players.items():
			for unit_name, unit in unit_names.items():

				if unit_name not in units:
					meta[unit_name] = {}
					units[unit_name] = {}

				if guild_name not in units[unit_name]:
					units[unit_name][guild_name] = {}

				meta[unit_name]['url']        = unit['url']
				meta[unit_name]['translated'] = unit['name']

				units[unit_name][guild_name][player_name] = unit

	msgs = []
	for unit_name, guilds in units.items():
		for guild_name, player_names in guilds.items():

			lines = []
			lines.append(config['separator'])
			lines.append('`|%s| GP\u00a0 |Lv|GL|RT|Player`' % '*')

			rosters = sorted(player_names.items(), key=lambda x: x[1]['gp'], reverse=True)
			for player_name, unit in rosters:
				pad_gp = (5 - len(str(unit['gp']))) * '\u00a0'
				pad_gear = (2 - len(str(unit['gear']))) * '\u00a0'
				pad_level = (2 - len(str(unit['level']))) * '\u00a0'
				pad_relic = (2 - len(str(unit['relic']))) * '\u00a0'
				lines.append('`|%s|%s%d|%s%d|%s%d|%s%d|`**`%s`**' % (unit['rarity'], pad_gp, unit['gp'], pad_level, unit['level'], pad_gear, unit['gear'], pad_relic, unit['relic'], player_name))

			if not len(rosters):
				lines.append('No player found with characters matching your search criteria.')

			msgs.append({
				'title': '',
				'author': {
					'name': unit_name,
					'icon_url': images[unit_name]
				},
				'description': '**[%s](%s)**\n%s\n%s (%d)\n%s' % (meta[unit_name]['translated'], meta[unit_name]['url'], config['separator'], guild_name, len(player_names), '\n'.join(lines)),
			})

	if not msgs:
		msgs.append({
			'title': 'No Matching Unit',
			'description': 'No player found with characters matching your search criteria.',
		})

	return msgs
