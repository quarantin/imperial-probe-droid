#!/usr/bin/python3

import json

from opts import *
from errors import *
from constants import EMOJIS
from collections import OrderedDict
from utils import dotify, get_stars_as_emojis, add_stats, ROMAN_NUMBERS
from swgohgg import get_avatar_url
from swgohhelp import fetch_players, fetch_roster, get_ability_name, fetch_crinolo_stats

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
		'cumul-gp': 0,
		'char': {
			'levels': {},
			'stars': {},
		},
		'ship': {
			'levels': {},
			'stars': {},
		},
		'levels': {},
		'gears': {},
		'stars': {},
		'zetas': {},
	}

	for i in range(0, 85 + 1):
		stats['levels'][i] = 0
		stats['char']['levels'][i] = 0
		stats['ship']['levels'][i] = 0

	for i in range(0, 12 + 1):
		stats['gears'][i] = 0


	for i in range(0, 7 + 1):
		stats['stars'][i] = 0
		stats['char']['stars'][i] = 0
		stats['ship']['stars'][i] = 0

	for base_id, unit in roster.items():

		gp    = unit['gp']
		typ   = unit['type'] == 1 and 'char' or 'ship'
		level = unit['level']
		gear  = unit['gearLevel']
		stars = unit['starLevel']
		zetas = unit['zetas']

		stats['count'] += 1
		stats['cumul-gp'] += gp
		stats['levels'][level] += 1
		stats['gears'][gear] += 1
		stats['stars'][stars] += 1

		stats[typ]['levels'][level] += 1
		stats[typ]['stars'][stars] += 1

		for zeta in zetas:

			zeta_id = zeta['id']
			zeta_name = get_ability_name(config, zeta_id, lang)
			if zeta_name not in stats['zetas']:
				stats['zetas'][zeta_name] = 0
			stats['zetas'][zeta_name] += 1

	return stats

def get_stat_detail(name, stats, percent=False):

	coef = 1
	percent_sign = ''
	if percent is True:
		coef = 100
		percent_sign = '%'

	full_stat = name in stats['full'] and stats['full'][name] * coef or 0
	mods_stat = name in stats['mods'] and stats['mods'][name] * coef or 0
	gear_stat = name in stats['gear'] and stats['gear'][name] * coef or 0

	base_stat = round(full_stat, 3) - mods_stat - gear_stat

	if percent is True:

		string_stat = '+'.join([
			'%.02g' % base_stat,
			'%.02g' % mods_stat,
			'%.02g' % gear_stat,
		])

		#return '**`%.02g%%`** (`%s`)' % (round(full_stat, 3), string_stat)
		return '%.02g%%' % round(full_stat, 3)

	else:
		string_stat = '+'.join([
			'%d' % base_stat,
			'%d' % mods_stat,
			'%d' % gear_stat,
		])

		#return '**`%d`** (`%s`)' % (full_stat, string_stat)
		return '%d' % full_stat


def calc_def(d, key, level):

	armor = 0
	if key in d:
		armor = d[key]

	return armor / (armor + (7.5 * level)) * 100

def get_def_stat_detail(name, stats, level):

	base_stat = calc_def(stats['base'], name, level)
	mods_stat = calc_def(stats['mods'], name, level)
	gear_stat = calc_def(stats['gear'], name, level)
	full_stat = calc_def(stats['full'], name, level)

	string_stat = '+'.join([
		'%.02g' % base_stat,
		'%.02g' % mods_stat,
		'%.02g' % gear_stat,
	])

	#return '**`%.02g%%`** (`%s`)' % (full_stat, string_stat)
	return '%.02g%%' % full_stat

def get_cc_stat_detail(name, stats):

	rating_name = name.replace('Chance', 'Rating')

	mods_stat   = name        in stats['mods'] and stats['mods'][name]        or 0
	gear_stat   = rating_name in stats['gear'] and stats['gear'][rating_name] or 0
	base_stat   = rating_name in stats['base'] and stats['base'][rating_name] or 0
	full_stat   = rating_name in stats['full'] and stats['full'][rating_name] or 0

	if name not in stats['full']:
		if name == 'Physical Critical Chance':
			name = 'Physical Critical Rating'
		elif name == 'Special Critical Chance':
			name = 'Special Critical Rating'
		else:
			raise Exception('Unsupported stat: %s' % name)

	cc = ((full_stat / 2400 + 0.1) + stats['full'][name]) * 100

	#cc = round(cc, 3)

	mods_stat = round(mods_stat * 100, 3)
	gear_stat = round(((gear_stat / 2400) + 0.1) * 100, 3)
	base_stat = round(((base_stat / 2400) + 0.1) * 100 - 10, 3)

	string_stat = '+'.join([
		'%.02g' % base_stat,
		'%.02g' % mods_stat,
		'%.02g' % gear_stat,
	])

	#return '**`%.02g%%`** (`%s`)' % (cc, string_stat)
	return '%.02g%%' % cc

def get_cd_stat_detail(name, stats):

	base_stat   = (name in stats['base'] and stats['base'][name] or 0) * 100
	mods_stat   = (name in stats['mods'] and stats['mods'][name] or 0) * 100
	gear_stat   = (name in stats['gear'] and stats['gear'][name] or 0) * 100
	full_stat   = (name in stats['full'] and stats['full'][name] or 0) * 100

	string_stat = '+'.join([
		'%d' % base_stat,
		'%d' % mods_stat,
		'%d' % gear_stat,
	])

	#return '**`%d%%`** (`%s`)' % (full_stat, string_stat)
	return '%d%%' % full_stat

def unit_to_dict(config, player, roster, stats, base_id, lang):

	res = OrderedDict()

	res['Players'] = player['name']

	spacer = EMOJIS['']
	if base_id in roster:
		unit = roster[base_id]

		res['Stars'] = get_stars_as_emojis(unit['starLevel'])
		res['GP']     = '%d'  % unit['gp']
		res['Level']  = '%d' % unit['level']
		res['Gear']   = '%s' % unit['gearLevel']

		stat = stats[base_id]
		add_stats(stat)

		level = player['roster'][base_id]['level']

		# Health, Protection, Armor, Resistance
		res['Health']     = get_stat_detail('Health',         stat)
		res['Protection'] = get_stat_detail('Protection',     stat)
		res['Armor']      = get_def_stat_detail('Armor',      stat, level)
		res['Resistance'] = get_def_stat_detail('Resistance', stat, level)

		# Speed
		res['Speed'] = get_stat_detail('Speed', stat)

		# Potency, Tenacity
		res['Potency']  = get_stat_detail('Potency',  stat, percent=True)
		res['Tenacity'] = get_stat_detail('Tenacity', stat, percent=True)

		# CD, CC, Damage
		res['Phys.Damage']     = get_stat_detail('Physical Damage',             stat)
		res['Spec.Damage']     = get_stat_detail('Special Damage',              stat)
		res['CD']              = get_cd_stat_detail('Critical Damage',          stat)
		res['CC.Phys']         = get_cc_stat_detail('Physical Critical Chance', stat)
		res['CC.Spec']         = get_cc_stat_detail('Special Critical Chance',  stat)

		# Abilities
		for skill in player['roster'][base_id]['skills']:
			is_zeta = skill['isZeta']
			skill_tier = skill['tier']
			emoji = ' `\u00a0L%d\u00a0` ' % skill_tier
			if skill_tier == 8:
				emoji = is_zeta and EMOJIS['zeta'] or EMOJIS['omega']

			skill_name = get_ability_name(config, skill['id'], lang)
			res[skill_name] = emoji
	else:
		key = 'Unit still locked'
		res = { key: player['name'] }

	return res

def player_to_embedfield(config, player, roster, crinolo_stats, lang):

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
	res['GP']         = player['gp']['total']
	res['Char GP']    = player['gp']['char']
	res['Ship GP']    = player['gp']['ship']
	res['Level']      = player['level']
	res['Rank']       = player['arena']['char']['rank']
	res['Fleet Rank'] = player['arena']['ship']['rank']
	res['Guild']      = guild_name

	for star in reversed(range(1, 7 + 1)):
		stars = get_stars_as_emojis(star)
		res[stars] = stats['char']['stars'][star]

	res['L85 Units'] = stats['char']['levels'][85]

	gears = [ 1 ]
	gears.extend(range(7, 12 + 1))
	for gear in reversed(gears):
		gear_label = 'G%d Units' % gear
		res[gear_label] = stats['gears'][gear]

	res['Zetas'] = len(stats['zetas'])

	for star in reversed(range(1, 7 + 1)):
		stars = get_stars_as_emojis(star)
		res[stars] = stats['ship']['stars'][star]

	res['L85 Ships'] = stats['ship']['levels'][85]

	return res

def cmd_player_compare(config, author, channel, args):

	msgs = []

	args, players, error = parse_opts_players(config, author, args, expected_allies=2)
	if error:
		return error

	args, selected_units = parse_opts_unit_names(config, args)
	if args:
		return error_unknown_parameters(args)

	fields = []
	ally_codes = [ player.ally_code for player in players ]
	players_data = fetch_players(config, ally_codes)
	rosters = fetch_roster(config, ally_codes)
	stats = fetch_crinolo_stats(config, ally_codes)

	lang = 'eng_us'
	try:
		p = Player.objects.get(discord_id=author.id)
		lang = p.language
	except Player.DoesNotExist:
		pass

	for ally_code, player in players_data.items():
		fields.append(player_to_embedfield(config, player, rosters[ally_code], stats[ally_code], lang))

	player_fields = OrderedDict()
	for field in fields:
		for key, val in field.items():
			if key not in player_fields:
				player_fields[key] = []
			player_fields[key].append(str(val))

	max_key_len = 0
	for key in player_fields:
		if len(key) > max_key_len:
			max_key_len = len(key)

	lines = []
	for key, listval in player_fields.items():
		pad = (max_key_len - len(key)) + 1
		if key.startswith('★'):
			lines.append('**%s**`:| %s`' % (key, ' | '.join(listval)))
		else:
			lines.append('**`%s`**`:%s| %s`' % (key, pad * '\u00a0', ' | '.join(listval)))

	msgs.append({
		'title': 'Player Comparison',
		'description': '\n'.join(lines),
	})

	for unit in selected_units:

		units = []
		fields = OrderedDict()
		for ally_code, player in players_data.items():
			units.append(unit_to_dict(config, player, rosters[ally_code], stats[ally_code], unit['base_id'], lang))

		for someunit in units:
			for key, val in someunit.items():
				if key not in fields:
					fields[key] = []
				fields[key].append(val)

		max_key_len = 0
		for key in fields:
			if len(key) > max_key_len:
				max_key_len = len(key)

		lines = []

		key = 'Unit still locked'
		if key in fields:
			listval = fields.pop(key)
			pad = 1
			lines.append('**`%s`**`:%s%s`' % (key, pad * '\u00a0', ' | '.join(listval)))
			if fields:
				lines.append('')

		for key, listval in fields.items():
			pad = (max_key_len - len(key)) + 1
			if key in base_stats:
				lines.append('**`%s`**`:%s| %s`' % (key, pad * '\u00a0', ' | '.join(listval)))
			else:
				lines.append('**`%s`**`:%s|`%s' % (key, pad * '\u00a0', '` | `'.join(listval)))

		msgs.append({
			'author': {
				'name': unit['name'],
				'icon_url': get_avatar_url(unit['base_id']),
			},
			'description': '\n'.join(lines),
		})

	return msgs
