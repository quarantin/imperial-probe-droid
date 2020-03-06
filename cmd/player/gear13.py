from opts import *
from errors import *

from swgohgg import get_full_avatar_url
from swgohhelp import fetch_players, get_ability_name, get_unit_name

import DJANGO
from swgoh.models import Gear13Stat

from collections import OrderedDict

help_gear13 = {
	'title': 'Gear13 Help',
	'description': """Shows most popular gear 13 units that you don't already have.

**Syntax**
```
%prefixgear13 [player] [locked] [limit]```
**Aliases**
```
%prefixg13```
**Options**
**`limit:`** The max number of gear 13 you want to see (default is 25).
**`locked:`** If present, shows most popular gear 13 for units still locked.

**Examples**
Show top 25 most popular gear 13 for characters you have:
```
%prefixg13```
Show top 5 most popular gear 13 units:
```
%prefixg13 5```
Show top 25 most popular gear 13 for characters you don't have:
```
%prefixg13 locked```"""
}

def parse_opts_limit(request):

	args = request.args
	args_cpy = list(args)
	for arg in args_cpy:
		try:
			limit = int(arg)
			args.remove(arg)
			return limit

		except:
			pass

	return 25

def parse_opts_include_locked(request):

	args = request.args
	args_cpy = list(args)
	for arg in args_cpy:

		larg = arg.lower()
		if larg == 'locked' or larg == 'l':
			args.remove(arg)
			return True

	return False

def cmd_gear13(request):

	args = request.args
	author = request.author
	config = request.config

	language = parse_opts_lang(request)

	limit = parse_opts_limit(request)
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
				'gear': 1,
			},
		},
	})

	msgs = []
	all_g13 = OrderedDict()
	for g13 in Gear13Stat.objects.all().order_by('-percentage').values():
		unit_id = g13['unit_id']
		g13['locked'] = True
		unit = BaseUnit.objects.get(id=unit_id)
		all_g13[unit.base_id] = g13

	for ally_code_str, player in players.items():

		g13_list = dict(all_g13)

		for base_id, unit in player['roster'].items():

			if unit['gear'] == 13:
				del g13_list[base_id]
				continue

			if base_id not in g13_list:
				continue

			g13_list[base_id]['locked'] = False

		lines = []
		for base_id, g13 in g13_list.items():

			if g13['locked'] is not include_locked:
					continue

			unit_name = get_unit_name(base_id, language)
			percentage = g13['percentage']

			lines.append('`%.2f` **%s**' % (percentage, unit_name))

			limit -= 1
			if limit <= 0:
				break

		msgs.append({
			'title': 'Gear 13 Recommendations for %s' % player['name'],
			'description': '\n'.join(lines),
		})

	return msgs
