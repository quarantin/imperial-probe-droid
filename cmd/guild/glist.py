#!/usr/bin/python3

from opts import *
from utils import dotify

from swgohgg import get_avatar_url
from swgohhelp import fetch_guilds, fetch_roster, get_guilds_ally_codes, get_ability_name

help_guild_search = {
	'title': 'Guild Search Help',
	'description': """Search your guild for player matching some character requirements

**Syntax**
```
%prefixgs [players] [units] [filters]

**Examples**
Search your guild for all player having Asajj Ventress at least Gear 12:
```
%prefixgs 123456789 asajj g12```"""
}

def cmd_guild_search(config, author, channel, args):

	msgs = []

	args, lang = parse_opts_lang(args)
	args, ally_codes = parse_opts_ally_codes(config, author, args, min_allies=2)
	if not ally_codes:
		return [{
			'title': 'Missing Guild Code',
			'description': 'I need at least one guild code.',
		}]

	args, selected_units = parse_opts_unit_names(config, args)
	if not selected_units:
		return [{
			'title': 'Missing Unit Name',
			'description': 'I need at least one unit name.',
		}]
	
	args, selected_char_filters = parse_opts_char_filters(config, args)
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
			for ally_code in guild['roster']:
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
