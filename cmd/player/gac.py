import json
from datetime import datetime

from opts import *
from errors import *
from utils import lpad
from swgohhelp import fetch_players

help_gac = {
	'title': 'Player GAC Help',
	'description': """Compare Grand Arena stats of different players.

**Syntax**
```
%prefixgac [players]```
**Examples**
Show your GAC stats:
```
%prefixgac```
Compare your GAC stats to another player:
```
%prefixgac 123456789```
Compare GAC stats of two different players:
```
%prefixgac 123456789 234567890```"""
}

wanted_stats = {
	'STAT_SEASON_PROMOTIONS_EARNED_NAME':     'Promotions',
	'STAT_SEASON_MOST_LEAGUE_SCORE_NAME':     'Score',
	'STAT_SEASON_LEAGUE_SCORE_NAME':          'Lifetime',
#	'STAT_SEASON_BEST_RANK_NAME':             'Best Rank',
	'STAT_SEASON_OFFENSIVE_BATTLES_WON_NAME': 'Off. Wins',
	'STAT_SEASON_SUCCESSFUL_DEFENDS_NAME':    'Def. Wins',
	'STAT_SEASON_UNDERSIZED_SQUAD_WINS_NAME': 'Undsz Wins',
	'STAT_SEASON_BANNERS_EARNED_NAME':        'Banners',
	'STAT_SEASON_TERRITORIES_DEFEATED_NAME':  'Cleared Terr.',
	'STAT_SEASON_FULL_CLEAR_ROUND_WINS_NAME': 'Full Clears',
}

wanted_info = {
	'seasonId':        'Season ID',
	'eventInstanceId': 'Date',
	'league':          'League',
	'eliteDivision':   'Elite',
	'seasonPoints':    'Score',
	'division':        'Division',
	'rank':            'Rank',
}

def get_stat(stats, key):

	for stat in stats:
		if stat['nameKey'] == key:
				return str(stat['value'])

	return str(0)

def get_division(division):
	return str(int(12 - division / 5))

def get_elite(elite):
	return elite and 'Yes' or 'No'

def get_season_date(event_id):
	# SEASON_004A:O1579816800000
	return datetime.fromtimestamp(int(event_id.split(':')[1][1:-3])).strftime('%Y-%m-%d')

def parse_season(data):

	zones, typ, ga, variant, season, season_index = data.split('_')

	return '%s %s %s' % (zones[0:2], typ, variant)

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
	history = {}

	for selected_player in selected_players:

		player = players[selected_player.ally_code]
		max_len = max(len(player['name']), 7)

		key = 'Players'
		if key not in result:
			result[key] = []
		result[key].append(lpad(player['name'], max_len))

		pstats = player['stats']
		for key, real_key in wanted_stats.items():

			if real_key not in result:
				result[real_key] = []

			value = get_stat(pstats, key)
			result[real_key].append(lpad(value, max_len))

		i = 1
		for entry in reversed(player['grandArena']):

			for key, real_key in wanted_info.items():
				the_real_key = real_key + str(i)
				if the_real_key not in history:
					history[the_real_key] = []

				value = str(entry[key])

				if the_real_key.startswith('Season ID'):
					value = parse_season(entry[key])

				elif key.startswith('division'):
					value = get_division(entry[key])

				elif key.startswith('elite'):
					value = get_elite(entry[key])

				elif key.startswith('eventInstanceId'):
					value = get_season_date(entry[key])

				history[the_real_key].append(lpad(value, max_len))

			i += 1

	lines = []

	names = result.pop('Players')
	lines.append('__**Players**__')
	lines.append('`|%s|`' % '|'.join(names))
	lines.append('')

	lines.append('__**General Statistics**__')
	for key, values in result.items():
		display = '|'.join(values)
		if key == 'Players':
			lines.append('`|%s|`' % display)
			lines.append(config['separator'])
		else:
			lines.append('`|%s|`__**%s**__' % (display, key))

	for i in range(1, 4):

		seasons = history.pop('Season ID%d' % i)
		dates = history.pop('Date%d' % i)

		title = '__**Season %s**__ (*%s*)' % (seasons[0], dates[0].strip())
		lines.append('')
		lines.append(title)

		for key, values in history.items():
			if not key.endswith(str(i)):
				continue

			display = '|'.join(values)
			lines.append('`|%s|`__**%s**__' % (display, key.replace(str(i), '')))

	lines.append('')

	return [{
		'title': 'GAC Stats',
		'description': '\n'.join(lines),
	}]
