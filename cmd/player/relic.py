from opts import *
from errors import *
from utils import http_get, translate

from swgohgg import get_full_avatar_url
from swgohhelp import fetch_players, get_ability_name, get_unit_name

import DJANGO
from swgoh.models import RelicStat

from collections import OrderedDict

help_relic = {
	'title': 'Relic Help',
	'description': """Shows most popular relic tiers you don't already have.

**Syntax**
```
%prefixrelic [player] [locked] [relic]```
**Aliases**
```
%prefixrr```
**Options**
**`locked:`** If present, shows most popular relic tiers for units still locked.
**`relic:`** The relic tier you want to see (default is 7).

**Examples**
Show top most popular relic tiers for characters you have:
```
%prefixrr```"""
}

MAX_RELIC = 7

def parse_opts_relic_tier(request):

	args = request.args
	args_cpy = list(args)
	for arg in args_cpy:

		try:
			relic = int(arg)
			args.remove(arg)
			return relic

		except:
			continue

	return MAX_RELIC

def parse_opts_include_locked(request):

	args = request.args
	args_cpy = list(args)
	for arg in args_cpy:

		larg = arg.lower()
		if larg == 'locked' or larg == 'l':
			args.remove(arg)
			return True

	return False

def cmd_relic(request):

	args = request.args
	author = request.author
	config = request.config

	language = parse_opts_lang(request)

	limit = 25
	relic_tier = parse_opts_relic_tier(request)
	relic_field = 'relic%d_percentage' % relic_tier
	relic_filter = '-%s' % relic_field
	include_locked = parse_opts_include_locked(request)

	selected_players, error = parse_opts_players(request, min_allies=1, max_allies=1)

	if error:
		return error

	if not selected_players:
		return error_no_ally_code_specified(config, author)

	if args:
		return error_unknown_parameters(args)

	ally_code = selected_players[0].ally_code
	players = fetch_players(config, {
		'allycodes': [ ally_code ],
		'project': {
			'allyCode': 1,
			'name': 1,
			'roster': {
				'defId': 1,
				'relic': 1,
			},
		},
	})

	msgs = []
	all_relic = OrderedDict()
	for relic in RelicStat.objects.all().order_by(relic_filter).values():
		unit_id = relic['unit_id']
		relic['locked'] = True
		unit = BaseUnit.objects.get(id=unit_id)
		all_relic[unit.base_id] = relic

	for ally_code_str, player in players.items():

		relic_list = dict(all_relic)

		for base_id, unit in player['roster'].items():

			if 'relic' in unit and unit['relic'] is not None and 'currentTier' in unit['relic'] and unit['relic']['currentTier'] >= relic_tier:
				del relic_list[base_id]
				continue

			if base_id not in relic_list:
				continue

			relic_list[base_id]['locked'] = False

		lines = []
		for base_id, relic in relic_list.items():

			if relic['locked'] is not include_locked:
					continue

			unit_name = get_unit_name(base_id, language)
			percentage = relic[relic_field]

			lines.append('`%.2f` **%s**' % (percentage, unit_name))

			limit -= 1
			if limit <= 0:
				break

		msgs.append({
			'title': 'Relic Recommendations for %s' % player['name'],
			'description': '\n'.join(lines),
		})

	return msgs