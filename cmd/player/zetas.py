from opts import *
from errors import *

from swgohgg import get_full_avatar_url
from swgohhelp import get_ability_name, get_unit_name

import DJANGO
from swgoh.models import ZetaStat

from collections import OrderedDict

help_zetas = {
	'title': 'Zetas Help',
	'description': """Shows most popular zetas that you don't already have.

**Syntax**
```
%prefixzetas [player] [locked] [limit]```
**Aliases**
```
%prefixz```
**Options**
**`limit:`** The max number of zetas you want to see (default is 25).
**`locked:`** If present, shows most popular zetas for units still locked.

**Examples**
Show top 25 most popular zetas for characters you have:
```
%prefixz```
Show top 5 most popular zetas:
```
%prefixz 5```
Show top 25 most popular zetas for characters you don't have:
```
%prefixz locked```"""
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

async def cmd_zetas(request):

	args = request.args
	author = request.author
	config = request.config
	bot = request.bot

	language = parse_opts_lang(request)

	limit_per_user = parse_opts_limit(request)
	include_locked = parse_opts_include_locked(request)

	selected_players, error = parse_opts_players(request)

	if error:
		return error

	if not selected_players:
		return error_no_ally_code_specified(config, author)

	if args:
		return error_unknown_parameters(args)

	ally_codes = [ x.ally_code for x in selected_players ]
	players = await bot.client.players(ally_codes=ally_codes)
	players = { x['allyCode']: x for x in players }

	msgs = []
	all_zetas = OrderedDict()
	for zeta in ZetaStat.objects.all().order_by('-of_all_this_unit').values():
		skill_id = zeta['skill_id']
		zeta['locked'] = True
		all_zetas[skill_id] = zeta

	for player in selected_players:

		zetas = dict(all_zetas)

		jplayer = players[player.ally_code]
		jroster = { x['defId']: x for x in jplayer['roster'] }

		for base_id, unit in jroster.items():
			for skill in unit['skills']:

				skill_id = skill['id']
				if skill_id not in zetas:
					continue

				if 'tier' not in skill:
					continue

				if skill['tier'] == 8:
					del zetas[skill_id]
					continue

				zetas[skill_id]['locked'] = False

		lines = []
		limit = limit_per_user
		for zeta_id, zeta in zetas.items():

			if zeta['locked'] is not include_locked:
				continue

			percent = zeta['of_all_this_unit']
			unit = BaseUnit.objects.get(pk=zeta['unit_id'])
			unit_name = get_unit_name(unit.base_id, language)
			skill_name = get_ability_name(zeta['skill_id'], language)

			lines.append('`%.2f` **%s** %s' % (percent, unit_name, skill_name))

			limit -= 1
			if limit <= 0:
				break

		msgs.append({
			'author': {
				'name': jplayer['name'],
			},
			'title': 'Most Popular Zetas',
			'description': '\n'.join(lines),
		})

	return msgs
