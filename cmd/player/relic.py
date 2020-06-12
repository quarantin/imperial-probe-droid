from utils import translate

import DJANGO
from swgoh.models import BaseUnit, RelicStat

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

async def cmd_relic(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	config = ctx.config

	per_user_limit = 25

	ctx.alt = bot.options.parse_alt(args)
	language = bot.options.parse_lang(ctx, args)

	relic_tier = bot.options.parse_relic_tier(args)
	relic_field = 'relic%d_percentage' % relic_tier
	relic_filter = '-%s' % relic_field

	include_locked = bot.options.parse_include_locked(args)

	selected_players, error = bot.options.parse_players(ctx, args)

	if error:
		return error

	if args:
		return bot.errors.unknown_parameters(args)

	if not selected_players:
		return bot.errors.no_ally_code_specified(ctx)

	ally_codes = [ x.ally_code for x in selected_players ]
	players = await bot.client.players(ally_codes=ally_codes)
	if not players:
		return bot.errors.ally_codes_not_found(ally_codes)

	players = { x['allyCode']: x for x in players }

	msgs = []
	all_relic = OrderedDict()
	for relic in RelicStat.objects.all().order_by(relic_filter).values():
		unit_id = relic['unit_id']
		relic['locked'] = True
		unit = BaseUnit.objects.get(id=unit_id)
		all_relic[unit.base_id] = relic

	for player in selected_players:

		limit = per_user_limit
		relic_list = dict(all_relic)
		jplayer = players[player.ally_code]
		jroster = { x['defId']: x for x in jplayer['roster'] }

		for base_id, unit in jroster.items():

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

			unit_name = translate(base_id, language)
			percentage = relic[relic_field]

			lines.append('`%.2f` **%s**' % (percentage, unit_name))

			limit -= 1
			if limit <= 0:
				break

		msgs.append({
			'author': {
				'name': jplayer['name'],
			},
			'title': 'Most Popular Relics %d' % relic_tier,
			'description': '\n'.join(lines),
		})

	return msgs
