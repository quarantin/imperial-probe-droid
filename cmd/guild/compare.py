from collections import OrderedDict

from opts import *
from errors import *
from constants import EMOJIS
from utils import dotify, get_banner_emoji, get_relic_tier, get_stars_as_emojis, roundup, translate
from swgohhelp import fetch_players, fetch_guilds, fetch_crinolo_stats, get_ability_name, sort_players

help_guild_compare = {
	'title': 'Guild Compare Help',
	'description': """Compare different guilds, optionally comparing their respective units.

**Syntax**
```
%prefixgc [players] [units]```
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

def get_unit_stats(config, roster, lang):

	stats = {
		'count': 0,
		'cumul-gp': 0,
		'levels': {},
		'gears': {},
		'relics': {},
		'stars': {},
		'zetas': {},
	}

	for unit_roster in roster:


		gp    = unit_roster['gp']
		level = unit_roster['level']
		gear  = unit_roster['gear']
		relic = get_relic_tier(unit_roster)
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

		if relic not in stats['relics']:
			stats['relics'][relic] = 0
		stats['relics'][relic] += 1

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

	zeta_emoji = EMOJIS['zeta']

	if base_id in roster:

		stats = get_unit_stats(config, roster[base_id], lang)

		seven_stars = get_stars_as_emojis(7)

		res['__GUILD__']  = get_banner_emoji(guild['bannerLogo'], guild['bannerColor'])
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
				if relic in stats['relics']:
					count = stats['relics'][relic]

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

MAX_GEAR = 13
MAX_RELIC = 7
MAX_LEVEL = 85
MAX_RARITY = 7

MOD_STATS = {
	5:  'speed',
	41: 'offense',
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

			if unit['combatType'] == 1:
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
				if skill['tier'] == 8:
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
	res['**Compared Guilds**']['__GUILD__']       = '%s (%s)' % (guild['name'], guild['members'])
	res['**Compared Guilds**']['**Banner**']      = get_banner_emoji(guild['bannerLogo'], guild['bannerColor'])
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

def cmd_guild_compare(config, author, channel, args):

	msgs = []

	language = parse_opts_lang(author)

	args, selected_players, error = parse_opts_players(config, author, args, expected_allies=2)

	args, selected_units = parse_opts_unit_names(config, args)

	if args:
		return error_unknown_parameters(args)

	if not selected_units:
		return error_no_unit_selected()

	if error:
		return error

	fields = []
	guild_list = fetch_guilds(config, {
		'allycodes': [ str(x.ally_code) for x in selected_players ],
		'project': {
			'id': 1,
			'gp': 1,
			'desc': 1,
			'name': 1,
			'members': 1,
			'message': 1,
			'guildName': 1,
			'bannerLogo': 1,
			'bannerColor': 1,
			'roster': {
				'gp': 1,
				'gpChar': 1,
				'gpShip': 1,
				'allyCode': 1,
				'level': 1,
			},
		},
	})

	ally_codes = [ x.ally_code for x in selected_players ]
	for dummy, guild in guild_list.items():
		for ally_code_str, player in guild['roster'].items():
			if player['allyCode'] not in ally_codes:
				ally_codes.append(player['allyCode'])

	"""
	players_raw = fetch_players(config, {
		'allycodes': ally_codes,
		'project': {
			'allyCode': 1,
			'name': 1,
			'roster': {
				'defId': 1,
				'gp': 1,
				'gear': 1,
				'level': 1,
				'rarity': 1,
				'relic': 1,
				'skills': 1,
				'combatType': 1,
				'mods': {
					'pips': 1,
				},
			},
		},
	}, sort=False)

	"""

	stats, players = fetch_crinolo_stats(config, ally_codes) #, players_raw)

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
	banners = gdata.pop('**Banner**')
	topics = gdata.pop('**Topic**')
	descrs = gdata.pop('**Description**')

	lines = []

	for alist in [ names ]:
		i = 0
		for banner in banners:
			lines.append('%s | **__%s__**' % (banner, alist[i]))
			lines.append('%s | %s' % (banner, topics[i]))
			lines.append('%s | %s' % (banner, descrs[i]))
			i += 1

	field = {
		'name': '**Compared Guilds**',
		'value': '\n'.join(lines),
	}

	fields = [ field ]

	for category, data in accu.items():
		lines = []
		lines.append('`|` %s `|`' % ' `|` '.join(banners))
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
