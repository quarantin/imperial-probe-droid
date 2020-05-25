from collections import OrderedDict

from opts import *
from swgohgg import get_full_avatar_url
from utils import translate, get_ability_name

import DJANGO
from swgoh.models import ZetaStat

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

def parse_opts_limit(ctx):

	args = ctx.args
	args_cpy = list(args)
	for arg in args_cpy:
		try:
			limit = int(arg)
			args.remove(arg)
			return limit

		except:
			pass

	return 25

def parse_opts_include_locked(ctx):

	args = ctx.args
	args_cpy = list(args)
	for arg in args_cpy:

		larg = arg.lower()
		if larg == 'locked' or larg == 'l':
			args.remove(arg)
			return True

	return False

async def cmd_zetas(ctx):

	args = ctx.args
	author = ctx.author
	config = ctx.config
	bot = ctx.bot

	language = parse_opts_lang(ctx)

	limit_per_user = parse_opts_limit(ctx)

	include_locked = parse_opts_include_locked(ctx)

	selected_players, error = parse_opts_players(ctx)

	if error:
		return error

	if not selected_players:
		return bot.errors.no_ally_code_specified(ctx)

	if args:
		return bot.errors.unknown_parameters(args)

	ally_codes = [ x.ally_code for x in selected_players ]
	players = await bot.client.players(ally_codes=ally_codes)
	if not players:
		msgs = []
		for ally_code in ally_codes:
			msgs.extend(bot.errors.ally_code_not_found(ally_code))
		return msgs

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
			unit_name = translate(unit.base_id, language)
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
