import json

from opts import *
from errors import *
from constants import EMOJIS, MAX_SKILL_TIER
from collections import OrderedDict
from utils import get_relic_tier, get_stars_as_emojis, roundup
from swgohhelp import fetch_crinolo_stats, get_ability_name

import DJANGO
from swgoh.models import BaseUnit, BaseUnitSkill

help_player_compare = {
	'title': 'Player Compare Help',
	'description': """Compare different players, optionally comparing their respective units.

**Syntax**
```
%prefixpc [players] [units]```
**Examples**
Compare your profile to another by ally code (assuming you're registered):
```
%prefixpc 123456789```
Compare two different players:
```
%prefixpc 123456789 234567890```
Compare two different players and show stats differences about Revan and Traya:
```
%prefixpc 123456789 234567891 revan traya```"""
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

def get_player_stats(config, roster, lang):

	stats = {
		'count': 0,
		'gp': 0,
		'char': {
			'levels': {},
			'stars': OrderedDict(),
			'gp': 0,
		},
		'ship': {
			'levels': {},
			'stars': OrderedDict(),
			'gp': 0,
		},
		'levels': {},
		'gears': {},
		'relics': {},
		'stars': {},
		'zetas': 0,
		'omegas': 0,
	}

	for i in range(0, 85 + 1):
		stats['levels'][i] = 0
		stats['char']['levels'][i] = 0
		stats['ship']['levels'][i] = 0

	for i in range(0, 13 + 1):
		stats['gears'][i] = 0


	for i in range(0, 7 + 1):
		stats['relics'][i] = 0

	for i in range(0, 7 + 1):
		stats['stars'][i] = 0
		stats['char']['stars'][i] = 0
		stats['ship']['stars'][i] = 0

	for base_id, unit in roster.items():

		gp     = unit['gp'] or 0
		typ    = unit['combatType'] == 1 and 'char' or 'ship'
		level  = unit['level']
		gear   = unit['gear']
		stars  = unit['rarity']
		skills = unit['skills']
		relic  = get_relic_tier(unit)

		stats['count']         += 1
		stats['gp']            += gp
		stats['levels'][level] += 1
		stats['gears'][gear]   += 1
		stats['relics'][relic] += 1
		stats['stars'][stars]  += 1

		stats[typ]['levels'][level] += 1
		stats[typ]['stars'][stars]  += 1
		stats[typ]['gp']            += gp

		for skill in skills:

			if 'tier' not in skill or skill['tier'] != MAX_SKILL_TIER:
				continue

			key = skill['isZeta'] and 'zetas' or 'omegas'
			stats[key] += 1

	return stats

def get_stat_detail(name, stats, percent=False):

	coef = 1
	percent_sign = ''
	if percent is True:
		coef = 100
		percent_sign = '%'

	final_stat = name in stats['stats']['final'] and stats['stats']['final'][name] * coef or 0

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

def unit_to_dict(config, player, roster, stats, base_id, lang):

	res = OrderedDict()

	res['Players'] = player['name']

	spacer = EMOJIS['']
	if base_id in roster:
		stat = stats[base_id]
		unit = roster[base_id]

		res['Stars'] = get_stars_as_emojis(unit['rarity'])
		res['GP']    = '%d'  % unit['gp']
		res['Level'] = '%d' % unit['level']
		res['Gear']  = '%d' % unit['gear']
		res['Relic'] = '%d' % get_relic_tier(unit)

		# Health, Protection, Armor, Resistance
		res['Health']     = get_stat_detail('Health',         stat)
		res['Protection'] = get_stat_detail('Protection',     stat)
		res['Armor']      = get_def_stat_detail('Armor',      stat)
		res['Resistance'] = get_def_stat_detail('Resistance', stat)

		# Speed
		res['Speed'] = get_stat_detail('Speed', stat)

		# Potency, Tenacity
		res['Potency']  = get_stat_detail('Potency',  stat, percent=True)
		res['Tenacity'] = get_stat_detail('Tenacity', stat, percent=True)

		# CD, CC, Damage
		res['Phys.Damage'] = get_stat_detail('Physical Damage',             stat)
		res['Spec.Damage'] = get_stat_detail('Special Damage',              stat)
		res['CD']          = get_cd_stat_detail('Critical Damage',          stat)
		res['CC.Phys']     = get_cc_stat_detail('Physical Critical Chance', stat)
		res['CC.Spec']     = get_cc_stat_detail('Special Critical Chance',  stat)

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
		for skill in stat['skills']:
			skill_id = skill['id']
			skill_tier = skill['tier']
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

def player_to_embedfield(config, player, roster, lang):

	stats = get_player_stats(config, roster, lang)

	guild_name = player['guildName'].strip()
	if guild_name:
		guild_name = '%s' % guild_name
	else:
		guild_name = '**No guild**'

	res = OrderedDict()

	res['ID']         = player['id']
	res['name']       = player['name']
	res['Ally Code']  = player['allyCode']
	res['GP']         = stats['gp']
	res['Char GP']    = stats['char']['gp']
	res['Ship GP']    = stats['ship']['gp']
	res['Level']      = player['level']
	res['Rank']       = player['arena']['char']['rank']
	res['Fleet Rank'] = player['arena']['ship']['rank']
	res['Guild']      = guild_name

	res['Characters'] = OrderedDict()
	for star in reversed(range(1, 7 + 1)):
		stars = get_stars_as_emojis(star)
		res['Characters'][stars] = stats['char']['stars'][star]

	res['L85 Units'] = stats['char']['levels'][85]

	gears = []
	gears.extend(range(9, 13 + 1))
	for gear in reversed(gears):
		gear_label = 'G%d Units' % gear
		res[gear_label] = stats['gears'][gear]

	relics = []
	relics.extend(range(1, 7 + 1))
	for relic in reversed(relics):
		relic_label = 'R%d Units' % relic
		res[relic_label] = stats['relics'][relic]

	res['Zetas'] = stats['zetas']
	res['Omegas'] = stats['omegas']

	res['Ships'] = OrderedDict()
	for star in reversed(range(1, 7 + 1)):
		stars = get_stars_as_emojis(star)
		res['Ships'][stars] = stats['ship']['stars'][star]

	res['L85 Ships'] = stats['ship']['levels'][85]

	return res

async def cmd_player_compare(request):

	args = request.args
	config = request.config

	lang = parse_opts_lang(request)

	selected_players, error = parse_opts_players(request, expected_allies=2)
	if error:
		return error

	selected_units = parse_opts_unit_names(request)
	if args:
		return error_unknown_parameters(args)

	fields = []
	ally_codes = [ player.ally_code for player in selected_players ]
	stats, players = await fetch_crinolo_stats(config, ally_codes)

	for player in players:
		ally_code = player['allyCode']
		fields.append(player_to_embedfield(config, player, stats[ally_code], lang))

	player_fields = OrderedDict()
	for field in fields:
		for key, val in field.items():
			if key not in player_fields:
				player_fields[key] = []
			if type(val) is not list:
				player_fields[key].append(val)
			else:
				player_fields[key].append(str(val))

	max_key_len = 0
	for key in player_fields:
		if len(key) > max_key_len:
			max_key_len = len(key)

	msgs = []
	lines = []
	for key, listval in player_fields.items():
		pad = (max_key_len - len(key)) + 1
		if key in [ 'Characters', 'Ships' ]:
			lines.append('')
			lines.append('**`%s`**' % key)
			values = OrderedDict()
			for d in listval:
				for k, v in d.items():
					if k not in values:
						values[k] = []
					values[k].append(str(v))

			for k, v in values.items():
				lines.append('**%s**`:| %s`' % (k, ' | '.join(v)))
		else:
			listval = [ '%s' % i for i in listval ]
			lines.append('**`%s`**`:%s| %s`' % (key, pad * '\u00a0', ' | '.join(listval)))

	msgs.append({
		'title': 'Player Comparison',
		'description': '\n'.join(lines),
	})

	for unit in selected_units:

		units = []
		fields = OrderedDict()
		for player in players:
			ally_code = player['allyCode']
			units.append(unit_to_dict(config, player, stats[ally_code], stats[ally_code], unit.base_id, lang))

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
