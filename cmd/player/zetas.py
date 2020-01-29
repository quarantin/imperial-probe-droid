from opts import *
from errors import *
from utils import http_get, translate

from swgohgg import get_full_avatar_url
from swgohhelp import fetch_players, get_ability_name, get_unit_name

import DJANGO
from swgoh.models import ZetaStat

from collections import OrderedDict

help_zetas = {
	'title': 'Zetas Help',
	'description': """Shows most popular zetas that you don't already have.

**Syntax**
```
%prefixzetas [player]```
**Aliases**
```
%prefixz```

**Examples**
```
%prefixz```"""
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

def cmd_zetas(request):

	args = request.args
	author = request.author
	config = request.config

	language = parse_opts_lang(request)

	limit = parse_opts_limit(request)

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
				'level': 1,
				'rarity': 1,
				'relic': 1,
				'skills': 1,
				'equipped': {
					'slot': 1,
				},
			},
		},
	})

	msgs = []
	all_zetas = OrderedDict()
	for zeta in ZetaStat.objects.all().order_by('-of_all_this_unit').values():
		skill_id = zeta['skill_id']
		zeta['locked'] = True
		all_zetas[skill_id] = zeta

	for ally_code_str, player in players.items():

		zetas = dict(all_zetas)

		for base_id, unit in player['roster'].items():
			for skill in unit['skills']:

				skill_id = skill['id']
				if skill_id not in zetas:
					continue

				if skill['tier'] == 8:
					del zetas[skill_id]
					continue

				zetas[skill_id]['locked'] = False

		lines = []
		for zeta_id, zeta in zetas.items():

			if zeta['locked'] is True:
				continue

			percent = zeta['of_all_this_unit']
			unit = BaseUnit.objects.get(pk=zeta['unit_id'])
			unit_name = get_unit_name(config, unit.base_id, language)
			skill_name = get_ability_name(config, zeta['skill_id'], language)

			lines.append('`%.2f` **%s** %s' % (percent, unit_name, skill_name))

			limit -= 1
			if limit <= 0:
				break

		msgs.append({
			'title': '',
			'description': '\n'.join(lines),
		})

	return msgs
