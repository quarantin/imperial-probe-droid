from collections import OrderedDict

from opts import *
from errors import *
from constants import EMOJIS, MAX_GEAR, MAX_LEVEL, MAX_RARITY, MAX_RELIC, MAX_SKILL_TIER
from utils import dotify, get_banner_emoji, get_stars_as_emojis, roundup, translate
from swgohhelp import fetch_guilds, fetch_crinolo_stats, get_ability_name, sort_players

import DJANGO
from swgoh.models import BaseUnitSkill

help_guild_compare = {
	'title': 'Guild Compare Help',
	'description': """Show units of selected guilds.

**Syntax**
```
%prefixgc [players] [units]```
**Examples**
Show stats for Darth Traya in your guild:
```
%prefixgc traya```
Show stats for Darth Traya in another guild:
```
%prefixfgc 123456789 traya```
Compare your guild stats for Darth Traya to another guild:
```
%prefixgc me 123456789 traya```"""
}

def get_unit_stats(config, roster, lang):

	stats = {
		'count': 0,
		'cumul-gp': 0,
		'levels': {},
		'gears': {},
		'relic': {},
		'stars': {},
		'zetas': {},
	}

	for unit in roster:


		gp    = unit['gp'] or 0
		level = unit['level']
		gear  = unit['gear']
		stars = unit['rarity']
		relic = BaseUnitSkill.get_relic(unit)
		zetas = BaseUnitSkill.get_zetas(unit)

		stats['count'] += 1
		stats['cumul-gp'] += gp

		if level not in stats['levels']:
			stats['levels'][level] = 0
		stats['levels'][level] += 1

		if gear not in stats['gears']:
			stats['gears'][gear] = 0
		stats['gears'][gear] += 1

		if relic not in stats['relic']:
			stats['relic'][relic] = 0
		stats['relic'][relic] += 1

		if stars not in stats['stars']:
			stats['stars'][stars] = 0
		stats['stars'][stars] += 1

		for zeta in zetas:

			zeta_id = zeta['id']
			zeta_name = get_ability_name(zeta_id, lang)
			if zeta_name not in stats['zetas']:
				stats['zetas'][zeta_name] = 0
			stats['zetas'][zeta_name] += 1

		if 85 not in stats['levels']:
			stats['levels'][85] = 0

	return stats

def unit_to_dict(config, guild, roster, base_id, lang):

	res = OrderedDict()

	zeta_emoji = EMOJIS['zeta']

	if base_id in roster:

		stats = get_unit_stats(config, roster[base_id], lang)

		seven_stars = get_stars_as_emojis(7)

		res['__GUILD__']  = '__**%s**__' % guild['name']
		res['**Avg.GP**'] = str(int(stats['cumul-gp'] / stats['count']))
		res['**Locked**'] = str(guild['members'] - stats['count'])
		res['**Count**']  = str(stats['count'])
		res['**Lvl85**']  = str(stats['levels'][85])
		res[seven_stars]  = str(7 in stats['stars'] and stats['stars'][7] or 0)

		if not BaseUnit.is_ship(base_id):
			for gear in reversed(range(MAX_GEAR - 2, MAX_GEAR + 1)):

				count = 0
				if gear in stats['gears']:
					count = stats['gears'][gear]

				res['**Gear %d**' % gear] = str(count)

			for relic in reversed(range(1, MAX_RELIC + 1)):

				count = 0
				if relic in stats['relic']:
					count = stats['relic'][relic]

				res['**Relic %d**' % relic] = str(count)

		if stats['zetas']:
			for zeta_name in stats['zetas']:
				count = stats['zetas'][zeta_name]
				zeta_str = '%s**%s**' % (zeta_emoji, zeta_name)
				res[zeta_str] = str(count)

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

async def cmd_guild_compare(request):

	args = request.args
	config = request.config

	language = parse_opts_lang(request)

	excluded_ally_codes = parse_opts_ally_codes_excluded(request)

	selected_players, error = parse_opts_players(request)
	if error:
		return error

	selected_units = parse_opts_unit_names(request)
	if not selected_units:
		return error_no_unit_selected()

	if args:
		return error_unknown_parameters(args)

	fields = []
	guild_list = await fetch_guilds(config, [ str(x.ally_code) for x in selected_players ])
	selectors = [ str(p.ally_code) for p in selected_players ]

	guilds = {}
	for selector in selectors:
		guild = guild_list[selector]
		guild_name = guild['name']
		guilds[guild_name] = guild

	ally_codes = []
	for selector in selectors:
		guild = guild_list[selector]
		for ally_code_str, player in guild['roster'].items():
			ally_code = player['allyCode']
			if ally_code not in ally_codes:
				ally_codes.append(ally_code)

	copy = list(ally_codes)
	for ally_code in copy:
		if ally_code in excluded_ally_codes:
			ally_codes.remove(ally_code)

	stats, players = await fetch_crinolo_stats(config, ally_codes, units=selected_units)

	players = sort_players(players)

	msgs = []
	for unit in selected_units:

		units = []
		unit_name = translate(unit.base_id, language)
		fields = OrderedDict()
		for guild_name, guild in guilds.items():

			roster = {}
			for dummy, dummy_player in guild['roster'].items():
				ally_code = dummy_player['allyCode']
				if ally_code not in players:
					print('WARN: Player missing from swgoh.help/api/players: %s' % ally_code)
					continue

				#player = players[ally_code]
				player = stats[ally_code]
				for base_id, player_unit in player.items():
					if base_id not in roster:
						roster[base_id] = []

					roster[base_id].append(player_unit)

			units.append(unit_to_dict(config, guild, roster, unit.base_id, language))

		for someunit in units:
			for key, val in someunit.items():
				if key not in fields:
					fields[key] = []
				fields[key].append(val)

		lines = []
		lines.append('**[%s](%s)**' % (unit_name, unit.get_url()))
		lines.append(config['separator'])
		first_time = True
		zeta_started = False
		for key, val in fields.items():

			newval = []
			for v in val:
				pad = max(0, 5 - len(str(v))) * '\u00a0'
				newval.append('%s%s' % (pad, v))

			if key == '__GUILD__':
				lines.append('`|` %s `|`%s' % ('|'.join(newval), ''))
			else:
				lines.append('`| %s |`%s' % ('|'.join(newval), key))

		msgs.append({
			'author': {
				'name': unit.name,
				'icon_url': unit.get_image(),
			},
			'description': '\n'.join(lines),
		})

	return msgs
