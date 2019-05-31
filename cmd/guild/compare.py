#!/usr/bin/python3

from collections import OrderedDict

from opts import *
from errors import *
from utils import dotify, get_stars_as_emojis
from swgohgg import get_avatar_url
from swgohhelp import fetch_players, fetch_guilds, get_ability_name

help_guild_compare = {
	'title': 'Guild Compare Help',
	'description': """Compare different guilds, optionally comparing their respective units.

**Syntax**
```
%prefixgc [players] [units]
**Examples**
Compare your guild to another (assuming you're registered):
```
%prefixgc 123456789```
Compare guilds from two different players:
```
%prefixgc 123456789 234567891```
Compare guilds from two different players and show differences about Revan and Traya:
```
%prefixgc 123456789 234567891 revan traya```"""
}

def get_guild_stats(config, roster, lang):

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
		gear  = unit_roster['gear']
		stars = unit_roster['rarity']
		zetas = [ x for x in unit_roster['skills'] if x['tier'] == 8 and x['isZeta'] ]

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

def unit_to_dict(config, guild, roster, base_id, lang):

	res = OrderedDict()

	if base_id in roster:

		stats = get_guild_stats(config, roster[base_id], lang)

		seven_stars = get_stars_as_emojis(7)

		res['Guild']    = guild['name']
		res['Avg. GP']  = str(int(stats['cumul-gp'] / stats['count']))
		res['Count']    = str(stats['count'])
		res['Level 85'] = str(stats['levels'][85])
		res[seven_stars]    = str(7 in stats['stars'] and stats['stars'][7] or 0)

		for gear in [ 12, 11, 10 ]:

			count = 0
			if gear in stats['gears']:
				count = stats['gears'][gear]

			res['Gear %d' % gear] = str(count)

		res['Locked'] = str(guild['members'] - stats['count'])

		if stats['zetas']:
			res['Zetas'] = ''
			for zeta_name in stats['zetas']:
				count = stats['zetas'][zeta_name]
				res[zeta_name] = str(count)

		"""
		for ability in sorted(stats['abilities']):

			lines.append('**%s** ' % ability)

			sublines = []
			#del(stats['abilities'][ability]['others'])
			for key in sorted(stats['abilities'][ability]):
				count = stats['abilities'][ability][key]
				sublines.append('%s: %s' % (key.title(), count))

			lines.append('- %s' % '\n - '.join(sublines))
		"""

	else:
		res['No one unlocked this unit yet.'] = ''

	return res

def guild_to_embedfield(guild):

	lines = [
		'**Guild ID:** %s' % guild['id'],
		'**Members: ** %s' % guild['members'],
		'**Profiles:** %s' % len(guild['roster']),
		#'**Avg.Levl:** %s' % guild['stats']['level'],
		#'**Avg.Rank:** %s' % guild['stats']['arena_rank'],
		'**Guild GP:** %s' % dotify(guild['gp']),
		#'**Units GP:** %s' % dotify(guild['stats']['character_galactic_power']),
		#'**Ships GP:** %s' % dotify(guild['stats']['ship_galactic_power']),
		#'**Raid won:** %s' % dotify(guild['stats']['guild_raid_won']),
		#'**PVP units:** %s' % dotify(guild['stats']['pvp_battles_won']),
		#'**PVP ships:** %s' % dotify(guild['stats']['ship_battles_won']),
		##'**PVE:** %s' % dotify(guild['stats']['pve_battles_won']),
		#'**PVE hard:** %s' % dotify(guild['stats']['pve_hard_won']),
		#'**Gal.Wars:** %s' % dotify(guild['stats']['galactic_war_won']),
		#'**Contribs:** %s' % dotify(guild['stats']['guild_contribution']),
		#'**Donations:** %s' % dotify(guild['stats']['guild_exchange_donations']),
		'**Topic:** %s' % guild['message'],
		'**Description:** %s' % guild['desc'],
		''
	]

	return {
		'name': guild['name'],
		'value': '\n'.join(lines),
		'inline': True,
	}

def cmd_guild_compare(config, author, channel, args):

	msgs = []

	lang = parse_opts_lang(author)

	args, selected_players, error = parse_opts_players(config, author, args, expected_allies=2)

	args, selected_units = parse_opts_unit_names(config, args)

	if args:
		return error_unknown_parameters(args)

	if not selected_units:
		return error_no_unit_selected()

	if error:
		return error

	fields = []
	ally_codes = [ player.ally_code for player in selected_players ]
	guild_list = fetch_guilds(config, ally_codes)

	members = []
	for ally_code, guild in guild_list.items():
		members.extend(list(guild['roster']))

	players = fetch_players(config, {
		'allycodes': members,
		'project': {
			'allyCode': 1,
			'name': 1,
			'roster': {
				'defId': 1,
				'gp': 1,
				'gear': 1,
				'level': 1,
				'rarity': 1,
				'skills': 1,
			},
		},
	})

	guilds = {}
	for ally_code, guild in guild_list.items():
		guild_name = guild['name']
		guilds[guild_name] = guild
		fields.append(guild_to_embedfield(guild))

	msgs.append({
		'title': 'Guild Comparison',
		'fields': fields,
	})

	for unit in selected_units:

		units = []
		fields = OrderedDict()
		for guild_name, guild in guilds.items():

			roster = {}
			for ally_code in guild['roster']:
				if ally_code not in players:
					print('WARN: Player missing from swgoh.help/api/players: %s' % ally_code)
					continue
				player = players[ally_code]
				for base_id, player_unit in player['roster'].items():
					if base_id not in roster:
						roster[base_id] = []

					roster[base_id].append(player_unit)

			units.append(unit_to_dict(config, guild, roster, unit.base_id, lang))

		for someunit in units:
			for key, val in someunit.items():
				if key not in fields:
					fields[key] = []
				fields[key].append(val)

		lines = []
		first_time = True
		for key, val in fields.items():

			newval = []
			for v in val:
				pad = 0
				if len(v) < 3:
					pad = 2 - len(v)
				newval.append('%s%s' % (pad * '\u00a0', v))

			key_str = '**`%s`**' % key
			if key == 'Guild':
				key_str = ''

			if first_time:
				first_time = False
				lines.append('**Stats**')
				lines.append(config['separator'])

			if key == 'Zetas':
				lines.append(config['separator'])
				lines.append('')
				lines.append('**%s**' % key)
				lines.append(config['separator'])

			else:
				lines.append('`|%s|`%s' % ('|'.join(newval), key_str))

		msgs.append({
			'title': '%s' % unit.name,
			'author': {
				'name': unit.name,
				'icon_url': get_avatar_url(unit.base_id),
			},
			'description': '\n'.join(lines),
		})

	return msgs
