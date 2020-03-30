import json

from opts import *
from errors import *
from swgohhelp import fetch_players

help_gac = {
	'title': 'Player GAC Help',
	'description': """Compare Grand Arena stats of different players.

**Syntax**
```
%prefixgac [players]```
**Examples**
Show your player stats:
```
%prefixgac```
Compare your player stats to another player:
```
%prefixgac 123456789```
Compare player stats of two different players:
```
%prefixgac 123456789 234567890```"""
}

wanted_stats = {
	'STAT_SEASON_LEAGUE_SCORE_NAME':          'Lifetime:            ',
	'STAT_SEASON_PROMOTIONS_EARNED_NAME':     'Promotions:          ',
	'STAT_SEASON_OFFENSIVE_BATTLES_WON_NAME': 'Offensive Wins:      ',
	'STAT_SEASON_SUCCESSFUL_DEFENDS_NAME':    'Defensive Wins:      ',
	'STAT_SEASON_BANNERS_EARNED_NAME':        'Banners:             ',
	'STAT_SEASON_FULL_CLEAR_ROUND_WINS_NAME': 'Full Clear:          ',
	'STAT_SEASON_UNDERSIZED_SQUAD_WINS_NAME': 'Undersized Wins:     ',
	'STAT_SEASON_TERRITORIES_DEFEATED_NAME':  'Territories Cleared: ',
	'STAT_SEASON_MOST_LEAGUE_SCORE_NAME':     'Season Score:        ',
	'STAT_SEASON_BEST_RANK_NAME':             'Best Rank:           ',
}

def get_stat(stats, key):

	for stat in stats:
		if stat['nameKey'] == key:
			if key == 'STAT_SEASON_BEST_RANK_NAME':
				return hex(stat['value']).replace('0x', '')
			else:
				return str(stat['value'])

	return str(0)

def list2str(alist):
	return '[' + ', '.join(alist) +']'

async def cmd_gac(request):

	args = request.args
	config = request.config

	lang = parse_opts_lang(request)

	selected_players, error = parse_opts_players(request, expected_allies=2)
	if error:
		return error

	fields = []
	ally_codes = [ player.ally_code for player in selected_players ]
	players = await fetch_players(config, ally_codes)

	result = {}

	for selected_player in selected_players:

		player = players[selected_player.ally_code]

		key = 'Players:' + (' ' * 13)
		if key not in result:
			result[key] = []
		result[key].append(player['name'])

		pstats = player['stats']
		for key, real_key in wanted_stats.items():

			if real_key not in result:
				result[real_key] = []

			result[real_key].append(get_stat(pstats, key))

	lines = []
	for key, values in result.items():
		lines.append('`%s%s`' % (key, list2str(values)))

	return [{
		'title': 'GAC Stats',
		'description': '\n'.join(lines),
	}]
