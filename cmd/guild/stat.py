from collections import OrderedDict

from opts import *
from errors import *
from constants import EMOJIS, MAX_GEAR, MAX_LEVEL, MAX_RARITY, MAX_RELIC, MAX_SKILL_TIER
from utils import dotify, get_banner_emoji, get_relic_tier, get_stars_as_emojis, roundup, translate
from swgohhelp import fetch_guilds, fetch_crinolo_stats, get_ability_name, sort_players

import DJANGO
from swgoh.models import BaseUnit

help_guild_stat = {
	'title': 'Guild Stat Help',
	'description': """Compare stats of different guilds.

**Syntax**
```
%prefixgs [players]```
**Examples**
Show your guild stats:
```
%prefixgs```
Compare stats of your guild with another guild:
```
%prefixgs 123456789```
Compare stats of two different guilds:
```
%prefixgs 123456789 234567891```"""
}

def get_guild_stats(guild, players):

	stats = {
		'gpChar': 0,
		'gpShip': 0,
		'level': 0,
		'omegas': 0,
		'zetas': 0,
		's7-units': 0,
		's7-ships': 0,
		'l85-units': 0,
		'l85-ships': 0,
		'g13-units': 0,
		'g12-units': 0,
		'g11-units': 0,
		'r0-units': 0,
		'r1-units': 0,
		'r2-units': 0,
		'r3-units': 0,
		'r4-units': 0,
		'r5-units': 0,
		'r6-units': 0,
		'r7-units': 0,
		'6-pips-mods': 0,
		'speed-arrows': 0,
		'speed-mods+20': 0,
		'speed-mods+25': 0,
		'offense-mods+100': 0,
		'offense-mods+150': 0,
	}

	for ally_code_str, profile in guild['roster'].items():
		ally_code = profile['allyCode']

		for key in [ 'gpChar', 'gpShip', 'level' ]:

			if key not in profile:
				print('WARN: Missing key `%s` in guild roster object for ally code: %s' % (key, ally_code))
				continue

			stats[key] += profile[key]

		if ally_code not in players:
			print('WARN: Ally code not found in guild: %s' % ally_code)
			continue

		player = players[ally_code]
		for base_id, unit in player['roster'].items():

			is_max_level  = (unit['level'] == MAX_LEVEL)
			is_max_rarity = (unit['rarity'] == MAX_RARITY)

			if not BaseUnit.is_ship(unit['defId']):
				stats['s7-units'] += (is_max_rarity and 1 or 0)
				stats['l85-units'] += (is_max_level and 1 or 0)
				if unit['gear'] == 13:
					stats['g13-units'] += 1
				elif unit['gear'] == 12:
					stats['g12-units'] += 1
				elif unit['gear'] == 11:
					stats['g11-units'] += 1

				relic = get_relic_tier(unit)
				stats['r%d-units' % relic] += 1
			else:
				stats['s7-ships'] += (is_max_rarity and 1 or 0)
				stats['l85-ships'] += (is_max_level and 1 or 0)

			for skill in unit['skills']:
				if 'tier' in skill and skill['tier'] == MAX_SKILL_TIER:
					key = 'omegas'
					if skill['isZeta']:
						key = 'zetas'
					stats[key] += 1

			if 'mods' in unit:
				for mod in unit['mods']:
					if mod['pips'] == 6:
						stats['6-pips-mods'] += 1

	guild.update(stats)

def guild_to_dict(guild, players):

	get_guild_stats(guild, players)

	res = OrderedDict()

	res['**Compared Guilds**'] = OrderedDict()
	res['**Compared Guilds**']['__GUILD__']       = '__**%s**__' % guild['name']
	res['**Compared Guilds**']['**Members**']     = str(guild['members'])
	res['**Compared Guilds**']['**Banner**']      = get_banner_emoji(guild['bannerLogo'])
	res['**Compared Guilds**']['**Topic**']       = guild['message']
	res['**Compared Guilds**']['**Description**'] = guild['desc']

	#'**Avg.Rank** %s'      % guild['stats']['arena_rank'],

	res['**Guild GP**'] = OrderedDict()
	res['**Guild GP**']['**Total**']      = dotify(guild['gp'])
	res['**Guild GP**']['**Characters**'] = dotify(guild['gpChar'])
	res['**Guild GP**']['**Ships**']      = dotify(guild['gpShip'])

	res['**Avg Player GP**'] = OrderedDict()
	res['**Avg Player GP**']['**Total**']      = dotify(guild['gp'] / len(guild['roster']))
	res['**Avg Player GP**']['**Characters**'] = dotify(guild['gpChar'] / len(guild['roster']))
	res['**Avg Player GP**']['**Ships**']      = dotify(guild['gpShip'] / len(guild['roster']))

	res['**Characters**'] = OrderedDict()
	res['**Characters**']['**7 Stars**']    = dotify(guild['s7-units'])
	res['**Characters**']['**Lvl 85**']     = dotify(guild['l85-units'])
	res['**Characters**']['**G13**']        = dotify(guild['g13-units'])
	res['**Characters**']['**G12**']        = dotify(guild['g12-units'])
	res['**Characters**']['**G11**']        = dotify(guild['g11-units'])

	for relic in reversed(range(1, MAX_RELIC + 1)):
		res['**Characters**']['**R%d**' % relic] = dotify(guild['r%d-units' % relic])

	res['**Characters**']['**Omegas**']     = dotify(guild['omegas'])
	res['**Characters**']['**Zetas**']      = dotify(guild['zetas'])
	res['**Characters**']['**6 Dot Mods**'] = dotify(guild['6-pips-mods'])

	res['**Ships**'] = OrderedDict()
	res['**Ships**']['**7 Star**'] = dotify(guild['s7-ships'])
	res['**Ships**']['**Lvl 85**'] = dotify(guild['l85-ships'])

	return res

async def cmd_guild_stat(request):

	args = request.args
	config = request.config

	language = parse_opts_lang(request)

	excluded_ally_codes = parse_opts_ally_codes_excluded(request)

	selected_players, error = parse_opts_players(request, expected_allies=2)
	if error:
		return error

	if args:
		return error_unknown_parameters(args)

	fields = []
	guild_list = await fetch_guilds(config, [ str(x.ally_code) for x in selected_players ])

	ally_codes = [ x.ally_code for x in selected_players ]
	for dummy, guild in guild_list.items():
		for ally_code_str, player in guild['roster'].items():
			ally_code = player['allyCode']
			if ally_code not in ally_codes:
				ally_codes.append(ally_code)

	copy = list(ally_codes)
	for ally_code in copy:
		if ally_code in excluded_ally_codes:
			ally_codes.remove(ally_code)

	stats, players = await fetch_crinolo_stats(config, ally_codes)

	players = sort_players(players)

	guilds = {}
	for ally_code, guild in guild_list.items():
		guild_name = guild['name']
		guilds[guild_name] = guild
		fields.append(guild_to_dict(guild, players))

	accu = {}
	for guild in fields:
		for category, data in guild.items():
			for key, line in data.items():
				if category not in accu:
					accu[category] = OrderedDict()
				if key not in accu[category]:
					accu[category][key] = []
				if line is not None:
					accu[category][key].append(line)

	gdata = accu.pop('**Compared Guilds**')
	names = gdata.pop('__GUILD__')
	members = gdata.pop('**Members**')
	banners = gdata.pop('**Banner**')
	topics = gdata.pop('**Topic**')
	descrs = gdata.pop('**Description**')

	lines = []

	for alist in [ names ]:
		i = 0
		for banner in banners:
			lines.append('%s | %s (%s)' % (banner, alist[i], members[i]))
			lines.append('%s | %s' % (banner, topics[i]))
			lines.append('%s | %s' % (banner, descrs[i]))
			i += 1

	field = {
		'name': '**Compared Guilds**',
		'value': '\n'.join(lines),
	}

	fields = [ field ]

	msgs = []
	for category, data in accu.items():
		lines = []
		lines.append('`|` %s `|`' % ' `|` '.join(names))
		for key, values in data.items():
			if key == '__GUILD__':
				key = ''

			newvals = []
			for val in values:
				pad = max(0, 11 - len(str(val))) * '\u00a0'
				newvals.append('%s%s' % (pad, val))

			lines.append('`|%s|`%s' % ('|'.join(newvals), key))

		fields.append({
			'name': category,
			'value': '\n'.join(lines),
		})

	msgs.append({
		'title': 'Guild Comparison',
		'fields': fields,
	})

	return msgs
