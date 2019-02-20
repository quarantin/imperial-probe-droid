#!/usr/bin/python3

import json

from opts import *
from constants import EMOJIS
from utils import dotify, get_stars_as_emojis, add_stats
from swgohgg import get_avatar_url
from swgohhelp import fetch_players, fetch_roster, get_guilds_ally_codes, get_ability_name, fetch_crinolo_stats

help_player_compare = {
	'title': 'Player Compare Help',
	'description': """Show statistics about one or more players, optionally comparing their respective units.

**Syntax**
```
%prefixpc [players] [units]```
**Examples**
Compare your profile to another by ally code:
```
%prefixpc 123456789```
Compare two different players:
```
%prefixpc 123456789 234567890```
Compare your profile to another and show stats about Revan and Darth Traya:
```
%prefixpc 123456789 revan traya```"""
}

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

def get_stat_detail(name, stats, percent=False, label=None):

	coef = 1
	percent_sign = ''
	if percent is True:
		coef = 100
		percent_sign = '%'

	if label is None:
		label = name

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

		return '%s: **`%.02g%%`** (`%s`)' % (label, round(full_stat, 3), string_stat)

	else:
		string_stat = '+'.join([
			'%d' % base_stat,
			'%d' % mods_stat,
			'%d' % gear_stat,
		])

		return '%s: **`%d`** (`%s`)' % (label, full_stat, string_stat)


def calc_def(d, key, level):

	armor = 0
	if key in d:
		armor = d[key]

	return armor / (armor + (7.5 * level)) * 100

def get_def_stat_detail(name, stats, level, label=None):

	if label is None:
		label = name

	base_stat = calc_def(stats['base'], name, level)
	mods_stat = calc_def(stats['mods'], name, level)
	gear_stat = calc_def(stats['gear'], name, level)
	full_stat = calc_def(stats['full'], name, level)

	string_stat = '+'.join([
		'%.02g' % base_stat,
		'%.02g' % mods_stat,
		'%.02g' % gear_stat,
	])

	return '%s: **`%.02g%%`** (`%s`)' % (label, full_stat, string_stat)

def get_cc_stat_detail(name, stats, label):

	rating_name = name.replace('Chance', 'Rating')

	mods_stat   = name        in stats['mods'] and stats['mods'][name]        or 0
	gear_stat   = rating_name in stats['gear'] and stats['gear'][rating_name] or 0
	base_stat   = rating_name in stats['base'] and stats['base'][rating_name] or 0
	full_stat   = rating_name in stats['full'] and stats['full'][rating_name] or 0

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

	return '%s: **`%.02g%%`** (`%s`)' % (label, cc, string_stat)

def get_cd_stat_detail(name, stats, label):

	base_stat   = (name in stats['base'] and stats['base'][name] or 0) * 100
	mods_stat   = (name in stats['mods'] and stats['mods'][name] or 0) * 100
	gear_stat   = (name in stats['gear'] and stats['gear'][name] or 0) * 100
	full_stat   = (name in stats['full'] and stats['full'][name] or 0) * 100

	string_stat = '+'.join([
		'%d' % base_stat,
		'%d' % mods_stat,
		'%d' % gear_stat,
	])

	return '%s: **`%d%%`** (`%s`)' % (label, full_stat, string_stat)

def unit_to_embedfield(config, player, roster, stats, base_id, lang):

	lines = []

	spacer = EMOJIS['']
	if base_id in roster:
		unit = roster[base_id]

		sublines = []
		sublines.append('**G%d**' % unit['gearLevel'])
		sublines.append('**L%d**' % unit['level'])
		sublines.append('**GP%d**'  % unit['gp'])

		info = '|'.join(sublines)
		stars = get_stars_as_emojis(unit['starLevel'])

		lines.append('%s %s' % (stars, info))

		stat = stats[base_id]
		add_stats(stat)

		level = player['roster'][base_id]['level']

		# Health, Protection, Armor, Resistance
		lines.append(get_stat_detail('Health',     stat))
		lines.append(get_stat_detail('Protection', stat))
		lines.append(get_def_stat_detail('Armor',      stat, level))
		lines.append(get_def_stat_detail('Resistance', stat, level))

		# Speed
		lines.append(get_stat_detail('Speed', stat))

		# Potency, Tenacity
		lines.append(get_stat_detail('Potency',  stat, percent=True))
		lines.append(get_stat_detail('Tenacity', stat, percent=True))

		# CD, CC, Damage
		lines.append(get_stat_detail('Physical Damage',             stat, label='Phys.Damage'))
		lines.append(get_stat_detail('Special Damage',              stat, label='Spec.Damage'))
		lines.append(get_cc_stat_detail('Physical Critical Chance', stat, label='CC.Phys'))
		lines.append(get_cc_stat_detail('Special Critical Chance',  stat, label='CC.Spec'))
		lines.append(get_cd_stat_detail('Critical Damage',          stat, label='CD'))

		# Abilities
		for skill in player['roster'][base_id]['skills']:
			emoji = spacer
			is_zeta = skill['isZeta']
			skill_tier = skill['tier']
			if skill_tier == 8:
				emoji = is_zeta and EMOJIS['zeta'] or EMOJIS['omega']

			skill_name = get_ability_name(config, skill['id'], lang)
			lines.append('%s %s\u202F' % (emoji, skill_name))
	else:
		lines.append('Character still locked.')

	return {
		'name': player['name'],
		'value': '\n'.join(lines),
		'inline': True,
	}

def player_to_embedfield(config, player, roster, crinolo_stats, lang):

	stats = get_player_stats(config, roster, lang)

	lines = [
		'**ID:** `%s`' % player['id'],
		'**Ally Code:** `%s`' % player['allyCode'],
		'**GP:** `%s`' % dotify(player['gp']['total']),
		'**Char GP:** `%s`' % dotify(player['gp']['char']),
		'**Ship GP:** `%s`' % dotify(player['gp']['ship']),
		'**Level:** `%s`' % player['level'],
		'**Rank:** `%s`' % player['arena']['char']['rank'],
		'**Fleet Rank:** `%s`' % player['arena']['ship']['rank'],
		'**Guild:** `%s`' % player['guildName'],
		'**Characters**',
	]

	for star in reversed(range(1, 7 + 1)):
		lines.append('%s: `%s`' % (get_stars_as_emojis(star), stats['char']['stars'][star]))

	lines.append('**L85 Units:** `%s`' % stats['char']['levels'][85])
	gears = [ 1 ]
	gears.extend(range(7, 12 + 1))
	for gear in reversed(gears):
		lines.append('**G%d Units:** `%s`' % (gear, stats['gears'][gear]))

	lines.append('**Zetas:** `%s`' % len(stats['zetas']))
	lines.append('')

	lines.append('**Ships**')

	for star in reversed(range(1, 7 + 1)):
		lines.append('%s: `%s`' % (get_stars_as_emojis(star), stats['ship']['stars'][star]))

	lines.append('**L85 Units:** `%s`' % stats['ship']['levels'][85])
	lines.append('')

	return {
		'name': player['name'],
		'value': '\n'.join(lines),
		'inline': True,
	}

def cmd_player_compare(config, author, channel, args):

	msgs = []

	args, lang = parse_opts_lang(args)
	args, ally_codes = parse_opts_ally_codes(config, author, args, min_allies=2)
	if not ally_codes:
		return [{
			'title': 'Not Found',
			'color': 'red',
			'description': 'No ally code specified or found registered to %s' % author,
		}]

	args, selected_units = parse_opts_unit_names(config, args)
	if args:
		plural = len(args) > 1 and 's' or ''
		return [{
			'title': 'Invalid Parameter%s' % plural,
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
		}]

	fields = []
	players = fetch_players(config, ally_codes)
	rosters = fetch_roster(config, ally_codes)
	stats = fetch_crinolo_stats(config, ally_codes)

	for ally_code, player in players.items():
		fields.append(player_to_embedfield(config, player, rosters[ally_code], stats[ally_code], lang))

	msgs.append({
		'title': 'Player Comparison',
		'fields': fields,
	})

	for unit in selected_units:

		fields = []
		for ally_code, player in players.items():
			fields.append(unit_to_embedfield(config, player, rosters[ally_code], stats[ally_code], unit['base_id'], lang))

		msgs.append({
			'author': {
				'name': unit['name'],
				'icon_url': get_avatar_url(unit['base_id']),
			},
			'fields': fields,
		})

	return msgs
