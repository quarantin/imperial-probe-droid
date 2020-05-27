import json
from collections import OrderedDict

from constants import EMOJIS, MAX_SKILL_TIER
from utils import get_stars_as_emojis, roundup, get_ability_name

import DJANGO
from swgoh.models import BaseUnit, BaseUnitSkill

help_player_compare = {
	'title': 'Player Compare Help',
	'description': """Show units of selected players.

**Syntax**
```
%prefixpc [players] [units]```
**Examples**
Show your bounty hunters:
```
%prefixpc bh```
Show bounty hunters of another player:
```
%prefixpc 123456789 bh```
Compare your bounty hunters to another player:
```
%prefixpc me 123456789 bh```"""
}

base_stats = [
	'Players',
	'Stars',
	'GP',
	'Level',
	'Gear',
	'Relic',
	'Health',
	'Protection',
	'Armor',
	'Resistance',
	'Speed',
	'Potency',
	'Tenacity',
	'Phys.Damage',
	'Spec.Damage',
	'CD',
	'CC.Phys',
	'CC.Spec',
	'Unit still locked',
]

def get_stat_detail(name, unit, percent=False):

	coef = 1
	percent_sign = ''
	if percent is True:
		coef = 100
		percent_sign = '%'

	final_stat = name in unit['stats']['final'] and unit['stats']['final'][name] * coef or 0

	if percent is True:

		#return '**`%.02g%%`** (`%s`)' % (round(final_stat, 3), string_stat)
		return '%s%%' % roundup(final_stat)

	else:
		#return '**`%d`** (`%s`)' % (final_stat, string_stat)
		return '%d' % final_stat


def get_def_stat_detail(name, stats):
	final_stat = name in stats['stats']['final'] and stats['stats']['final'][name] * 100 or 0
	return '%.02g%%' % final_stat

def get_cc_stat_detail(name, stats):
	final_stat = name in stats['stats']['final'] and stats['stats']['final'][name] * 100 or 0
	return '%.02g%%' % final_stat

def get_cd_stat_detail(name, stats):
	final_stat = (name in stats['stats']['final'] and stats['stats']['final'][name] or 0) * 100
	return '%d%%' % final_stat

def unit_to_dict(config, player, roster, base_id, lang):

	res = OrderedDict()

	res['Players'] = player['name']

	spacer = EMOJIS['']

	if base_id in roster:
		unit = roster[base_id]

		res['Stars'] = get_stars_as_emojis(unit['rarity'])
		res['GP']    = '%d'  % ('gp' in unit and unit['gp'] or 0)
		res['Level'] = '%d' % unit['level']
		res['Gear']  = '%d' % unit['gear']
		res['Relic'] = '%d' % BaseUnitSkill.get_relic(unit)

		# Health, Protection, Armor, Resistance
		res['Health']     = get_stat_detail('Health',         unit)
		res['Protection'] = get_stat_detail('Protection',     unit)
		res['Armor']      = get_def_stat_detail('Armor',      unit)
		res['Resistance'] = get_def_stat_detail('Resistance', unit)

		# Speed
		res['Speed'] = get_stat_detail('Speed', unit)

		# Potency, Tenacity
		res['Potency']  = get_stat_detail('Potency',  unit, percent=True)
		res['Tenacity'] = get_stat_detail('Tenacity', unit, percent=True)

		# CD, CC, Damage
		res['Phys.Damage'] = get_stat_detail('Physical Damage',             unit)
		res['Spec.Damage'] = get_stat_detail('Special Damage',              unit)
		res['CD']          = get_cd_stat_detail('Critical Damage',          unit)
		res['CC.Phys']     = get_cc_stat_detail('Physical Critical Chance', unit)
		res['CC.Spec']     = get_cc_stat_detail('Special Critical Chance',  unit)

		real_unit = BaseUnit.objects.get(base_id=base_id)
		unit_skills = BaseUnitSkill.objects.filter(unit=real_unit)
		for skill in unit_skills:
			skill_id = skill.skill_id
			skill_name = get_ability_name(skill_id, lang)
			res[skill_id] = {
				'tier': ' T0 ',
				'name': skill_name,
				'isZeta': skill.is_zeta,
			}

		# Abilities
		for skill in unit['skills']:
			skill_id = skill['id']
			skill_tier = 'tier' in skill and skill['tier'] or 0
			emoji = ' T%d ' % skill_tier
			if skill_tier == 8:
				emoji = '`%s`' % (skill['isZeta'] and EMOJIS['zeta'] or EMOJIS['omega'])

			if skill_id not in res:
				skill_name = get_ability_name(skill_id, lang)
				res[skill_id] = {
					'name': skill_name,
					'isZeta': False,
				}

			res[skill_id]['tier'] = emoji
	else:
		key = 'Unit still locked'
		res = { key: player['name'] }

	return res

async def cmd_player_compare(ctx):

	bot = ctx.bot
	args = ctx.args
	config = ctx.config

	lang = bot.options.parse_lang(ctx, args)

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
	players = await bot.client.players(ally_codes=ally_codes, units=selected_units, stats=True)
	players = { x['allyCode']: x for x in players }

	msgs = []
	for unit in selected_units:

		units = []
		fields = OrderedDict()
		for player in selected_players:

			ally_code = player.ally_code
			jplayer = players[ally_code]
			jroster = { x['defId']: x for x in jplayer['roster'] }

			units.append(unit_to_dict(config, jplayer, jroster, unit.base_id, lang))

		for someunit in units:
			for key, val in someunit.items():
				if key not in fields:
					fields[key] = []
				fields[key].append(val)

		lines = []

		key = 'Unit still locked'
		if key in fields:
			listval = fields.pop(key)
			pad = 1
			lines.append('**`%s`**`:%s%s`' % (key, pad * '\u00a0', ' | '.join(listval)))
			if fields:
				lines.append('')

		first_time = True
		for key, listval in fields.items():

			if key in base_stats:

				newlistval = []
				for item in listval:
					pad = 0
					aval = item
					if len(item) < 7 and key != 'Players':
						pad = max(0, 6 - len(item))
						aval = '%s%s ' % (pad * '\u00a0', item)

					newlistval.append(aval)

				if key == 'Players':
					lines.append('**Stats**')
					lines.append(config['separator'])

				key_string = '**`%s`**' % key
				if key in [ 'Players', 'Stars' ]:
					key_string = ''
				lines.append('`|%s|`%s' % ('|'.join(newlistval), key_string))
			else:
				if first_time:
					first_time = False
					lines.append(config['separator'])
					lines.append('')
					lines.append('**Skills**')
					lines.append(config['separator'])

				ability = listval[0]['name']
				tiers = [ x['tier'] for x in listval ]
				lines.append('`|%s|`**`%s`**' % ('|'.join(tiers), ability))

		msgs.append({
			'author': {
				'name': unit.name,
				'icon_url': unit.get_image(),
			},
			'description': '\n'.join(lines),
		})

	return msgs
