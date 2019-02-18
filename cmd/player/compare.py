#!/usr/bin/python3

from opts import *
from utils import dotify, get_stars_as_emojis
from swgohgg import get_avatar_url
from swgohhelp import fetch_players, fetch_roster, get_guilds_ally_codes, get_ability_name

help_player_compare = {
	'title': 'Player Compare Help',
	'description': """Show statistics about one or more players, optionally comparing their respective units.

**Syntax**
```
%prefixcompare [players] [units]
**Aliases**
```
%prefixc```
**Examples**
Compare your profile to another by ally code:
```
%prefixc 123456789```
Compare two different players:
```
%prefixc 123456789 234567890```
Compare your profile to another and show stats about Revan and Darth Traya:
```
%prefixc 123456789 revan traya```"""
}

def get_player_stats(config, roster, lang):

	stats = {
		'count': 0,
		'cumul-gp': 0,
		'levels': {},
		'gears': {},
		'stars': {},
		'zetas': {},
	}

	for unit_roster in roster:

		gp    = unit_roster['gp']
		level = unit_roster['level']
		gear  = unit_roster['gearLevel']
		stars = unit_roster['starLevel']
		zetas = unit_roster['zetas']

		stats['count'] += 1
		stats['cumul-gp'] += gp

		if level not in stats['levels']:
			stats['levels'][level] = 0
		stats['levels'][level] += 1

		if gear not in stats['gears']:
			stats['gears'][gear] = 0
		stats['gears'][gear] += 1

		if stars not in stats['stars']:
			stats['stars'][stars] = 0
		stats['stars'][stars] += 1

		for zeta in zetas:

			zeta_id = zeta['id']
			zeta_name = get_ability_name(config, zeta_id, lang)
			if zeta_name not in stats['zetas']:
				stats['zetas'][zeta_name] = 0
			stats['zetas'][zeta_name] += 1

	return stats

def unit_to_embedfield(config, player, roster, base_id, lang):

	lines = []

	if base_id in roster:
		unit_roster = roster[base_id]
		stats = get_player_stats(config, unit_roster, lang)
		lines.append(get_stars_as_emojis(next(iter(stats['stars']))))

		sublines = []
		sublines.append('G%d' % next(iter(stats['gears'])))
		sublines.append('L%d' % next(iter(stats['levels'])))
		sublines.append('GP%d'  % (stats['cumul-gp'] / stats['count']))
		lines.append(' '.join(sublines))

		if not stats['zetas']:
			lines.append('No zetas')
		else:
			lines.append('Zetas:')
			for zeta_name in stats['zetas']:
				lines.append('**%s**\u202F' % zeta_name)
	else:
		lines.append('Character still locked.')

	return {
		'name': player['name'],
		'value': '\n'.join(lines),
		'inline': True,
	}

def player_to_embedfield(player):

	lines = [
		'**ID:** %s' % player['id'],
		'**Ally Code:** %s' % player['allyCode'],
		'**GP:** %s' % dotify(player['gp']['total']),
		'**Char GP:** %s' % dotify(player['gp']['char']),
		'**Ship GP:** %s' % dotify(player['gp']['ship']),
		'**Level:** %s' % player['level'],
		'**Rank:** %s' % player['arena']['char']['rank'],
		'**Fleet Rank:** %s' % player['arena']['ship']['rank'],
		'**Guild:** %s' % player['guildName'],
		''
	]

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

	for ally_code, player in players.items():
		fields.append(player_to_embedfield(player))

	msgs.append({
		'title': 'Player Comparison',
		'fields': fields,
	})

	for unit in selected_units:

		fields = []
		for ally_code, player in players.items():

			roster = {}
			player_roster = rosters[int(ally_code)]
			for base_id, player_unit in player_roster.items():
				if base_id not in roster:
					roster[base_id] = []

				roster[base_id].append(player_unit)

			fields.append(unit_to_embedfield(config, player, roster, unit['base_id'], lang))

		msgs.append({
			'author': {
				'name': unit['name'],
				'icon_url': get_avatar_url(unit['base_id']),
			},
			'fields': fields,
		})

	return msgs
