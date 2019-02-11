#!/usr/bin/python3

from opts import *
from swgoh import *

help_guild_compare = {
	'title': 'Compare Two Guilds',
	'description': """Show statistics about two different guilds

**Syntax**
```
%prefixgcompare <guild ID> [other guild ID] [units]
**Aliases**
```
%prefixgc```
**Examples**
Compare your guild to another by guild ID:
```
%prefixgc 12345```
Compare two guilds by their guild ID:
```
%prefixgc 12345 67890```
Compare your guild to another by guild ID and show stats about Revan and Traya:
```
%prefixgc 12345 revan traya```"""
}

def dotify(number):
	return '{:,}'.format(number)

def unit_to_embedfield(guild, unit):

	lines = []

	name = unit['name']
	if name in guild['units']:
		stats = guild['units'][name]
		lines.append('Count: %d' % stats['count'])
		lines.append('Level 85: %d' % stats['levels'][85])

		for rarity in [ 7, 6, 5 ]:

			count = 0
			if rarity in stats['rarities']:
				count = stats['rarities'][rarity]

			lines.append('Rarity %d\*: %d' % (rarity, count))

		for gear in [ 12, 11, 10 ]:

			count = 0
			if gear in stats['gears']:
				count = stats['gears'][gear]

			lines.append('Gear %d: %d' % (gear, count))

		lines.append('Locked: %d' % (guild['member_count'] - stats['count']))

		for ability in sorted(stats['abilities']):

			lines.append('**%s** ' % ability)

			sublines = []
			#del(stats['abilities'][ability]['others'])
			for key in sorted(stats['abilities'][ability]):
				count = stats['abilities'][ability][key]
				sublines.append('%s: %s' % (key.title(), count))

			lines.append('- %s' % '\n - '.join(sublines))

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
		'**Members: ** %s' % guild['member_count'],
		'**Profiles:** %s' % guild['profile_count'],
		'**Avg.Levl:** %s' % guild['stats']['level'],
		'**Avg.Rank:** %s' % guild['stats']['arena_rank'],
		'**Profiles:** %s' % guild['profile_count'],
		'**Guild GP:** %s' % dotify(guild['galactic_power']),
		'**Units GP:** %s' % dotify(guild['stats']['character_galactic_power']),
		'**Ships GP:** %s' % dotify(guild['stats']['ship_galactic_power']),
		'**Raid won:** %s' % dotify(guild['stats']['guild_raid_won']),
		'**PVP units:** %s' % dotify(guild['stats']['pvp_battles_won']),
		'**PVP ships:** %s' % dotify(guild['stats']['ship_battles_won']),
		'**PVE:** %s' % dotify(guild['stats']['pve_battles_won']),
		'**PVE hard:** %s' % dotify(guild['stats']['pve_hard_won']),
		'**Gal.Wars:** %s' % dotify(guild['stats']['galactic_war_won']),
		'**Contribs:** %s' % dotify(guild['stats']['guild_contribution']),
		'**Donations:** %s' % dotify(guild['stats']['guild_exchange_donations']),
		''
	]

	return {
		'name': guild['name'],
		'value': '\n'.join(lines),
		'inline': True,
	}

def cmd_guild_compare(config, author, channel, args):

	msgs = []
	guilds = {}

	args, guild_codes = parse_opts_guild_codes(config, author, args)
	if not guild_codes:
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
	for guild_code in guild_codes:

		guilds[guild_code] = get_guild(guild_code)
		if not guilds[guild_code]:
			url = 'https://swgoh.gg/g/%s/' % guild_code
			return [{
				'title': 'Invalid Guild Code',
				'color': 'red',
				'description': 'Are you sure `%s` is a valid guild code and at least one player of this guild is registered on swgoh.gg? Please check this URL to verify: %s' % (guild_code, url),
			}]

		guild = guilds[guild_code]
		fields.append(guild_to_embedfield(guild))

	msgs.append({
		'title': 'Guild Comparison',
		'fields': fields,
	})

	for unit in selected_units:
		fields = []
		for guild_code in guild_codes:

			guild = guilds[guild_code]
			fields.append(unit_to_embedfield(guild, unit))

		msgs.append({
			'title': '%s' % unit['name'],
			'author': {
				'name': unit['name'],
				'icon_url': get_avatar_url(unit['base_id']),
			},
			'fields': fields,
		})

	return msgs