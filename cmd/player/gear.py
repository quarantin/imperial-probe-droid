from utils import translate

import json
from swgohgg import get_full_avatar_url, get_swgohgg_unit_url

import DJANGO
from swgoh.models import BaseUnitGear

help_gear = {
	'title': 'Gear Help',
	'description': """Shows gear needed for a given character.

**Syntax**
```
%prefixgear [unit]```
**Aliases**
```
%prefixg```

**Examples**
Show gear needed for count dooku:
```
%prefixg count dooku```"""
}

def get_gear_levels(base_id):
	result = {}

	gear_levels = BaseUnitGear.objects.filter(unit__base_id=base_id)
	for gear_level in gear_levels:
		unit_name = gear_level.unit.name
		if unit_name not in result:
			result[unit_name] = {
				'url': get_swgohgg_unit_url(gear_level.unit.base_id),
				'tiers': {},
			}

		tier = gear_level.tier
		if tier not in result[unit_name]['tiers']:
			result[unit_name]['tiers'][tier] = {}

		slot = gear_level.slot
		gear_id = gear_level.gear.base_id

		result[unit_name]['tiers'][tier][slot] = {
			'gear': gear_id,
			'url': gear_level.gear.get_url(),
		}

	return result

async def cmd_gear(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	config = ctx.config

	ctx.alt = bot.options.parse_alt(args)
	language = bot.options.parse_lang(ctx, args)

	selected_players, error = bot.options.parse_players(ctx, args)

	selected_units = bot.options.parse_unit_names(args)

	if error:
		return error

	if args:
		return bot.errors.unknown_parameters(args)

	if not selected_players:
		return bot.errors.no_ally_code_specified(ctx)

	if not selected_units:
		return bot.errors.no_unit_selected(ctx)

	ally_codes = [ x.ally_code for x in selected_players ]
	players = await bot.client.players(ally_codes=ally_codes)
	if not players:
		return bot.errors.ally_codes_not_found(ally_codes)

	players = { x['allyCode']: x for x in players }

	msgs = []
	for player in selected_players:

		jplayer = players[player.ally_code]
		jroster = { x['defId']: x for x in jplayer['roster'] }

		for unit in selected_units:

			lines = []
			fields = []
			player_unit = unit.base_id in jroster and jroster[unit.base_id] or {}
			gear_levels = get_gear_levels(unit.base_id)
			for name, data in gear_levels.items():
				unit_name = translate(unit.base_id, language)
				lines.append('**[%s](%s)**' % (unit_name, get_swgohgg_unit_url(unit.base_id)))
				min_gear_level = player_unit and player_unit['gear'] or 1
				for tier in reversed(range(min_gear_level, 13)):
					sublines = []
					for slot in sorted(data['tiers'][tier]):
						gear_id = data['tiers'][tier][slot]['gear']
						gear_url = data['tiers'][tier][slot]['url']
						gear_name = translate(gear_id, language)
						equipped = False
						if player_unit:
							for gear in player_unit['equipped']:
								if tier == player_unit['gear']:
									# gear['slot'] is an index, so add one for comparison
									if int(slot) == gear['slot'] + 1:
										equipped = True
										break

						bold = not equipped and '**' or ''

						sublines.append('%sSlot%s: [%s](%s)%s' % (bold, slot, gear_name, gear_url, bold))

					gear_tier_id = 'Unit_Tier%02d' % tier
					gear_tier_title = translate(gear_tier_id, language)

					fields.append({
						'name': '== %s ==' % gear_tier_title,
						'value': '\n'.join(sublines),
					})

			if not fields:
				lines.append('Maximum gear level.')

			msgs.append({
				#'title': '== Needed Gear ==',
				'description': '\n'.join(lines),
				'author': {
					'name': unit.name,
					'icon_url': unit.get_image(),
				},
				'image': {
					'url': get_full_avatar_url(config, unit, player_unit),
				},
				'fields': fields,
			})

	return msgs
