import json

from constants import EMOJIS, MAX_GEAR_LEVEL, MAX_LEVEL, MAX_RARITY, MAX_RELIC, MAX_SKILL_TIER
from collections import OrderedDict
from utils import get_stars_as_emojis

import DJANGO
from swgoh.models import BaseUnit, BaseUnitSkill

help_player_stat = {
	'title': 'Player Stat Help',
	'description': """Show stats of selected players.

**Syntax**
```
%prefixps [players]```
**Examples**
Show your player stats:
```
%prefixps```
Show stats of another player:
```
%prefixps 123456789```
Compare your stats to another player:
```
%prefixps me 234567890```"""
}

def get_player_stats(config, roster, lang):

	stats = {}

	stats['char'] = {}
	stats['ship'] = {}

	stats['levels'] = {}
	stats['char']['levels'] = {}
	stats['ship']['levels'] = {}
	for i in range(0, MAX_LEVEL + 1):
		stats['levels'][i] = 0
		stats['char']['levels'][i] = 0
		stats['ship']['levels'][i] = 0

	stats['gears'] = {}
	for i in range(0, MAX_GEAR_LEVEL + 1):
		stats['gears'][i] = 0

	stats['relic'] = {}
	for i in range(0, MAX_RELIC + 1):
		stats['relic'][i] = 0

	stats['stars'] = {}
	stats['char']['stars'] = {}
	stats['ship']['stars'] = {}
	for i in range(0, MAX_RARITY + 1):
		stats['stars'][i] = 0
		stats['char']['stars'][i] = 0
		stats['ship']['stars'][i] = 0

	stats['gp'] = 0
	stats['char']['gp'] = 0
	stats['ship']['gp'] = 0
	stats['count'] = 0
	stats['omegas'] = 0
	stats['zetas'] = 0
	for base_id, unit in roster.items():

		gp     = 'gp' in unit and unit['gp'] or 0
		typ    = unit['isShip'] and 'ship' or 'char'
		level  = unit['level']
		gear   = unit['gear']
		stars  = unit['rarity']
		skills = unit['skills']
		relic  = BaseUnitSkill.get_relic(unit)

		stats['gp']            += gp
		stats['count']         += 1
		stats['levels'][level] += 1
		stats['gears'][gear]   += 1
		stats['relic'][relic] += 1
		stats['stars'][stars]  += 1

		stats[typ]['levels'][level] += 1
		stats[typ]['stars'][stars]  += 1
		stats[typ]['gp']            += gp

		for skill in skills:

			if 'tier' not in skill or skill['tier'] != MAX_SKILL_TIER:
				continue

			key = BaseUnitSkill.is_zeta_ability(skill['id']) and 'zetas' or 'omegas'
			stats[key] += 1

	return stats

def parse_gac_season(season_id):

	zones, variant, dummy1, layout, dummy2, season = season_id.split('_')

	return zones, variant, layout, int(season)

def player_to_embedfield(config, player, roster, lang):

	stats = get_player_stats(config, roster, lang)

	guild_name = player['guildName'].strip()
	guild_name = guild_name and '%s' % guild_name or '**No guild**'

	res = OrderedDict()

	res['name']       = player['name']
	res['Ally Code']  = player['allyCode']
	res['Guild']      = guild_name
	res['GP']         = stats['gp']
	res['Char GP']    = stats['char']['gp']
	res['Ship GP']    = stats['ship']['gp']
	res['Level']      = player['level']
	res['Squad Rank'] = player['arena']['char']['rank']
	res['Fleet Rank'] = player['arena']['ship']['rank']

	res['Characters'] = OrderedDict()
	for star in reversed(range(1, MAX_RARITY + 1)):
		stars = get_stars_as_emojis(star)
		res['Characters'][stars] = stats['char']['stars'][star]

	res['L85 Units'] = stats['char']['levels'][85]

	gears = []
	gears.extend(range(9, MAX_GEAR_LEVEL + 1))
	for gear in reversed(gears):
		gear_label = 'G%d Units' % gear
		res[gear_label] = stats['gears'][gear]

	relic_list = []
	relic_list.extend(range(1, MAX_RELIC + 1))
	for relic in reversed(relic_list):
		relic_label = 'R%d Units' % relic
		res[relic_label] = stats['relic'][relic]

	res['Zetas'] = stats['zetas']
	res['Omegas'] = stats['omegas']

	res['Ships'] = OrderedDict()
	for star in reversed(range(1, MAX_RARITY + 1)):
		stars = get_stars_as_emojis(star)
		res['Ships'][stars] = stats['ship']['stars'][star]

	res['L85 Ships'] = MAX_LEVEL in stats['ship']['levels'] and stats['ship']['levels'][MAX_LEVEL] or 0

	return res

def get_player_division(division):
	return 12 - (division / 10)

async def cmd_player_stat(ctx):

	bot = ctx.bot
	args = ctx.args
	config = ctx.config

	lang = bot.options.parse_lang(ctx, args)

	selected_players, error = bot.options.parse_players(ctx, args)

	if error:
		return error

	if args:
		return bot.errors.unknown_parameters(args)

	if not selected_players:
		return bot.errors.no_ally_code_specified(ctx)

	fields = []
	ally_codes = [ x.ally_code for x in selected_players ]
	players = await bot.client.players(ally_codes=ally_codes, stats=True)
	if not players:
		return bot.errors.ally_codes_not_found(ally_codes)

	players = { x['allyCode']: x for x in players }

	for player in selected_players:
		jplayer = players[player.ally_code]
		jroster = { x['defId']: x for x in jplayer['roster'] }
		fields.append(player_to_embedfield(config, jplayer, jroster, lang))

	player_fields = OrderedDict()
	for field in fields:
		for key, val in field.items():
			if key not in player_fields:
				player_fields[key] = []
			if type(val) is not list:
				player_fields[key].append(val)
			else:
				player_fields[key].append(str(val))

	max_key_len = 0
	for key in player_fields:
		if len(key) > max_key_len:
			max_key_len = len(key)

	msgs = []
	lines = []
	for key, listval in player_fields.items():
		pad = (max_key_len - len(key)) + 1
		if key in [ 'Characters', 'Ships' ]:
			lines.append('')
			lines.append('**`%s`**' % key)
			values = OrderedDict()
			for d in listval:
				for k, v in d.items():
					if k not in values:
						values[k] = []
					values[k].append(str(v))

			for k, v in values.items():
				lines.append('**%s**`:| %s`' % (k, ' | '.join(v)))
		elif key in [ 'Grand Arena' ]:
			lines.append('')
			lines.append('**`%s`**' % key)
			for d in listval:
				lifetime = d['Lifetime']
				history = d['History']
				for gac in history:
					title = 'Season %d' % gac['season']
					lines.append('**`%s`**' % title)
					lines.append('`Rank:   %s`' % gac['rank'])
					lines.append('`Points: %s`' % gac['points'])
					lines.append('`League: %s`' % gac['league'])
					lines.append('`Division: %s`' % get_player_division(gac['division']))
					lines.append('`Variant: %s %s %s`' % (gac['zones'], gac['variant'], gac['layout']))

		else:
			listval = [ '%s' % i for i in listval ]
			lines.append('**`%s`**`:%s| %s`' % (key, pad * '\u00a0', ' | '.join(listval)))

	msgs.append({
		'title': 'Player Comparison',
		'description': '\n'.join(lines),
	})

	return msgs
