#!/usr/bin/python3

from opts import *
from utils import dotify
from swgohgg import get_avatar_url
from swgohhelp import fetch_guilds, fetch_roster, get_guilds_ally_codes, get_ability_name

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

def unit_to_embedfield(config, guild, roster, base_id, lang):

	lines = []

	if base_id in roster:
		unit_roster = roster[base_id]
		stats = get_guild_stats(config, unit_roster, lang)
		lines.append('Avg. GP: %d'  % (stats['cumul-gp'] / stats['count']))
		lines.append('Count: %d'    % stats['count'])
		lines.append('Level 85: %d' % stats['levels'][85])
		lines.append('7\*: %d'      % (7 in stats['stars'] and stats['stars'][7] or 0))

		for gear in [ 12, 11, 10 ]:

			count = 0
			if gear in stats['gears']:
				count = stats['gears'][gear]

			lines.append('Gear %d: %d' % (gear, count))

		lines.append('Locked: %d' % (guild['members'] - stats['count']))

		lines.append('Zetas:')
		for zeta_name in stats['zetas']:

			count = stats['zetas'][zeta_name]

			lines.append('%d x %s' % (count, zeta_name))
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
		lines.append('No one unlocked this unit yet.')

	return {
		'name': guild['name'],
		'value': '\n'.join(lines),
		'inline': True,
	}

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

	args, lang = parse_opts_lang(args)
	args, ally_codes = parse_opts_ally_codes(config, author, args, min_allies=2)
	if not ally_codes:
		return [{
			'title': 'Missing Guild Code',
			'description': 'I need at least one guild code.',
		}]

	args, selected_units = parse_opts_unit_names(config, args)
	if args:
		plural = len(args) > 1 and 's' or ''
		return [{
			'title': 'Invalid Parameter%s' % plural,
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
		}]

	fields = []
	guild_list = fetch_guilds(config, ally_codes)

	members = []
	for ally_code in guild_list:
		guild = guild_list[ally_code]
		allies = list(guild['roster'])
		members.extend(allies)
		fetch_roster(config, allies)

	roster_list = fetch_roster(config, members)

	guilds = {}
	for ally_code in guild_list:
		guild = guild_list[ally_code]
		guild_name = guild['name']
		guilds[guild_name] = guild
		fields.append(guild_to_embedfield(guild))

	msgs.append({
		'title': 'Guild Comparison',
		'fields': fields,
	})

	for unit in selected_units:

		fields = []
		for guild_name, guild in guilds.items():

			roster = {}
			for ally_code in roster_list:
				rosters = roster_list[ally_code]
				for base_id, player_unit in rosters.items():
					if base_id not in roster:
						roster[base_id] = []

					roster[base_id].append(player_unit)

			fields.append(unit_to_embedfield(config, guild, roster, unit['base_id'], lang))

		msgs.append({
			'title': '%s' % unit['name'],
			'author': {
				'name': unit['name'],
				'icon_url': get_avatar_url(unit['base_id']),
			},
			'fields': fields,
		})

	return msgs
