from utils import translate
from swgohgg import get_swgohgg_player_unit_url
from constants import MODSETS_NEEDED

DEFAULT_MIN_GEAR_LEVEL = 9

help_modcheck = {
	'title': 'Modcheck Help',
	'description': """Shows weak mod setups for the supplied ally codes.

**Syntax**
```
%prefixmodcheck [players] [options]```
**Aliases**
```
%prefixmc```
**Options**
**`count`** (or **`c`**): To show how many equipped mods.
**`missing`** (or **`m`**): To show units with missing mods.
**`nomods`** (or **`n`**): To show units with no mods.
**`incomplete`** (or **`i`**): To show units with incomplete modsets.
**`level`** (or **`l`**): To show units with mods less than level 15.
**`5pips`** (or **`5`**): To show units with mods less than 5 pips.
**`6pips`** (or **`6`**): To show units with mods less than 6 pips.
**`tier`** (or **`t`**): To show units with mods less than gold quality.
**`gear<1-13>`** (or **`g<1-13>`**): Minimun gear level to consider (default is **`g""" + str(DEFAULT_MIN_GEAR_LEVEL) + """`**).
If no option is specified, the following options will be selected by default:
Count, missing, incomplete, level and 5pips.

**Examples**
```
%prefixmc
%prefixmc @Someone
%prefixmc gear11
%prefixmc 123456789 missing
%prefixmc nomods
%prefixmc incomplete```""",
}

MAX_MOD_LEVEL = 15
MAX_MODS_PER_UNIT = 6
MIN_LEVEL_FOR_MODS = 50

def get_mod_stats(roster, min_gear_level):

	modcount = 0
	unitcount = 0
	units_with_no_mods = []
	units_with_missing_mods = []
	units_with_incomplete_modsets = []
	units_with_incomplete_modlevels = []
	units_with_mods_less_5_pips = []
	units_with_mods_less_6_pips = []
	units_with_mods_weak_tier = []

	import json
	for base_id, unit in roster.items():

		if unit['isShip'] or unit['level'] < MIN_LEVEL_FOR_MODS or unit['gear'] < min_gear_level:
			continue

		unit['weak-tier'] = []
		unit['mods-not-5-pips'] = []
		unit['mods-not-6-pips'] = []
		unit['mods-no-max-level'] = []

		modcount += len(unit['mods'])
		unitcount += 1

		if not unit['mods']:
			units_with_no_mods.append(unit)
			continue

		unit['missing-mods'] = MAX_MODS_PER_UNIT - len(unit['mods'])
		if unit['missing-mods'] > 0:
			units_with_missing_mods.append(unit)

		modsets = {}
		for mod in unit['mods']:

			if mod['pips'] < 5:
				unit['mods-not-5-pips'].append(mod)
				if unit not in units_with_mods_less_5_pips:
					units_with_mods_less_5_pips.append(unit)

			if mod['pips'] < 6:

				if mod['tier'] < 5:
					unit['weak-tier'].append(mod)
					if unit not in units_with_mods_weak_tier:
						units_with_mods_weak_tier.append(unit)

				unit['mods-not-6-pips'].append(mod)
				if unit not in units_with_mods_less_6_pips:
					units_with_mods_less_6_pips.append(unit)

			if mod['level'] < MAX_MOD_LEVEL:
				unit['mods-no-max-level'].append(mod)
				if unit not in units_with_incomplete_modlevels:
					units_with_incomplete_modlevels.append(unit)

			modset = mod['set']
			if modset not in modsets:
				modsets[modset] = 0

			modsets[modset] += 1

		for modset, count in modsets.items():
			needed = MODSETS_NEEDED[modset]
			if count % needed != 0 and unit not in units_with_missing_mods:
				units_with_incomplete_modsets.append(unit)
				break

	return modcount, unitcount, units_with_no_mods, units_with_missing_mods, units_with_incomplete_modsets, units_with_incomplete_modlevels, units_with_mods_less_5_pips, units_with_mods_less_6_pips, units_with_mods_weak_tier

async def cmd_modcheck(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	channel = ctx.channel
	config = ctx.config

	msgs = []
	units_with_missing_mods = []
	units_with_incomplete_modsets = []

	language = bot.options.parse_lang(ctx, args)

	modcheck = bot.options.parse_modcheck(args)

	min_gear_level = bot.options.parse_min_gear_level(args)

	selected_players, error = bot.options.parse_players(ctx, args)

	if error:
		return error

	if args:
		return bot.errors.unknown_parameters(args)

	if not selected_players:
		return bot.errors.no_ally_code_specified(ctx)

	ally_codes = [ p.ally_code for p in selected_players ]
	players = await bot.client.players(ally_codes=ally_codes)
	if not players:
		return bot.errors.ally_codes_not_found(ally_codes)

	players = { x['allyCode']: x for x in players }

	for player in selected_players:

		lines = []
		jplayer = players[player.ally_code]
		jroster = { x['defId']: x for x in jplayer['roster'] }
		ally_code = jplayer['allyCode']

		modcount, unitcount, units_with_no_mods, units_with_missing_mods, units_with_incomplete_modsets, units_with_incomplete_modlevels, units_with_mods_less_5_pips, units_with_mods_less_6_pips, units_with_mods_weak_tier = get_mod_stats(jroster, min_gear_level)


		if 'count' in modcheck:
			unitplural = unitcount > 1 and 's' or ''
			lines.append('**%d** unit%s match.' % (unitcount, unitplural))
			lines.append('**%d** equipped mods.' % modcount)

		lines.append('Minimum gear level: **%d**' % min_gear_level)
		lines.append(config['separator'])

		if 'nomods' in modcheck:

			sublines = []
			for unit in units_with_no_mods:
				unit_name = translate(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code, unit['defId'])
				sublines.append('**[%s](%s)** (No mods)' % (unit_name, unit_url))

			if not sublines:
				lines.append('No units found without any mods.')

			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		if 'missing' in modcheck:

			sublines = []
			for unit in units_with_missing_mods:
				unit_name = translate(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code, unit['defId'])
				sublines.append('**[%s](%s)** (**%d** missing)' % (unit_name, unit_url, unit['missing-mods']))

			if not sublines:
				lines.append('No units found with missing mods.')

			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		if 'incomplete' in modcheck:

			sublines = []
			for unit in units_with_incomplete_modsets:
				unit_name = translate(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code, unit['defId'])
				sublines.append('**[%s](%s)** (Incomplete modset)' % (unit_name, unit_url))

			if not sublines:
				lines.append('No units found with incomplete modsets.')

			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		if 'level' in modcheck:

			sublines = []
			for unit in units_with_incomplete_modlevels:
				unit_name = translate(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code, unit['defId'])
				plural = len(unit['mods-no-max-level']) > 1 and 's' or ''
				sublines.append('**[%s](%s)** (**%d** mod%s < L15)' % (unit_name, unit_url, len(unit['mods-no-max-level']), plural))

			if not sublines:
				lines.append('No units found with mods less than level 15.')

			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		if '5pips' in modcheck:

			sublines = []
			for unit in units_with_mods_less_5_pips:
				unit_name = translate(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code, unit['defId'])
				plural = len(unit['mods-not-5-pips']) > 1 and 's' or ''
				sublines.append('**[%s](%s)** (**%d** mod%s < 5 pips)' % (unit_name, unit_url, len(unit['mods-not-5-pips']), plural))

			if not sublines:
				lines.append('No units found with mods less than 5 pips.')

			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		if '6pips' in modcheck:

			sublines = []
			for unit in units_with_mods_less_6_pips:
				unit_name = translate(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code, unit['defId'])
				plural = len(unit['mods-not-6-pips']) > 1 and 's' or ''
				sublines.append('**[%s](%s)** (**%d** mod%s < 6 pips)' % (unit_name, unit_url, len(unit['mods-not-6-pips']), plural))

			if not sublines:
				lines.append('No units found with mods less than 6 pips.')

			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		if 'tier' in modcheck:

			sublines = []
			for unit in units_with_mods_weak_tier:
				unit_name = translate(unit['defId'], language)
				unit_url = get_swgohgg_player_unit_url(ally_code, unit['defId'])
				plural = len(unit['weak-tier']) > 1 and 's' or ''
				sublines.append('**[%s](%s)** (**%d** mod%s < Gold)' % (unit_name, unit_url, len(unit['weak-tier']), plural))

			if not sublines:
				lines.append('No units found with mods tier less than gold.')

			lines.extend(sorted(sublines))
			lines.append(config['separator'])

		lines = lines[0:-1]

		msgs.append({
			'title': '%s' % jplayer['name'],
			'description': '\n'.join(lines),
		})

	return msgs
