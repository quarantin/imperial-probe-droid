from collections import OrderedDict

from constants import EMOJIS, MAX_GEAR, MAX_LEVEL, MAX_RARITY, MAX_RELIC, MAX_SKILL_TIER
from utils import dotify, get_banner_emoji, get_stars_as_emojis, roundup, translate, get_ability_name

import DJANGO
from swgoh.models import BaseUnit, BaseUnitSkill

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
		'gp': 0,
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

	for ally_code, player in players.items():

		player_roster = {}
		for unit in player['roster']:

			base_id = unit['defId']

			if 'gp' in unit and unit['gp']:

				stats['gp'] += unit['gp']

				if unit['isShip']:
					stats['gpShip'] += unit['gp']

				else:
					stats['gpChar'] += unit['gp']

			player_roster[ base_id ] = unit

		for base_id, unit in player_roster.items():

			is_max_level  = (unit['level'] == MAX_LEVEL)
			is_max_rarity = (unit['rarity'] == MAX_RARITY)

			if not unit['isShip']:
				stats['s7-units'] += (is_max_rarity and 1 or 0)
				stats['l85-units'] += (is_max_level and 1 or 0)
				if unit['gear'] == 13:
					stats['g13-units'] += 1
				elif unit['gear'] == 12:
					stats['g12-units'] += 1
				elif unit['gear'] == 11:
					stats['g11-units'] += 1

				relic = BaseUnitSkill.get_relic(unit)
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
	res['**Compared Guilds**']['**Topic**']       = guild['topic']
	res['**Compared Guilds**']['**Description**'] = guild['description']

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

async def cmd_guild_stat(ctx):

	bot = ctx.bot
	args = ctx.args
	config = ctx.config

	ctx.alt = bot.options.parse_alt(args)
	language = bot.options.parse_lang(ctx, args)

	excluded_ally_codes = bot.options.parse_ally_codes_excluded(args)

	selected_players, error = bot.options.parse_players(ctx, args)

	if error:
		return error

	if args:
		return bot.errors.unknown_parameters(args)

	if not selected_players:
		return bot.errors.no_ally_code_specified(ctx)

	fields = []

	ally_codes = [ x.ally_code for x in selected_players ]
	guilds = await bot.client.guilds(ally_codes=ally_codes, stats=True)
	if not guilds:
		return bot.errors.ally_codes_not_found(ally_codes)

	result = {}
	for ally_code, guild in guilds.items():
		guild_name = guild['name']
		members = { x['id']: x for x in guild['members'] }
		result[guild_name] = guild
		fields.append(guild_to_dict(guild, members))

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
