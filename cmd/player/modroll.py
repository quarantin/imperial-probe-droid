from opts import *
from utils import translate
from constants import MODSLOTS, MODSETS, UNIT_STATS, EMOJIS

help_modroll= {
	'title': 'Modroll Help',
	'description': """List equipped mods having a secondary stat with 5 rolls.

**Syntax**
```
%prefixmodroll [players]```
**Aliases**
```
%prefixmr```
**Examples**
```
%prefixmodroll
%prefixmr```"""
}

MIN_ROLLS = 5

MOD_STATS = {
	5:  'speed',
	41: 'offense',
}

async def cmd_modroll(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	config = ctx.config

	msgs = []

	language = parse_opts_lang(ctx)

	selected_players, error = parse_opts_players(ctx)

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

	result = {}
	for ally_code, player in players.items():

		player_name = player['name']
		player_roster = { x['defId']: x for x in player['roster'] }

		for def_id, unit in player_roster.items():
			unit_name = translate(def_id, language)
			for mod in unit['mods']:
				for sec_stat in mod['secondaryStat']:
					if sec_stat['roll'] >= MIN_ROLLS:

						if player_name not in result:
							result[player_name] = {}

						if unit_name not in result[player_name]:
							result[player_name][unit_name] = []

						result[player_name][unit_name].append(mod)

	msgs = []
	for player_name, data in result.items():
		lines = []
		for unit_name, mods in sorted(data.items()):
			lines.append(unit_name)
			for mod in mods:
				slot = MODSLOTS[ mod['slot'] ].replace(' ', '').lower()
				slot_emoji = EMOJIS[slot]
				modset = MODSETS[ mod['set'] ].replace(' ', '').lower()
				modset_emoji = EMOJIS[modset]
				for sec in mod['secondaryStat']:
					if sec['roll'] >= MIN_ROLLS:
						stat_name = UNIT_STATS[ sec['unitStat'] ]
						stat_value = ('%.2f' % sec['value']).replace('.00', '')
						lines.append('%s%s %dD (%d) +%s %s' % (modset_emoji, slot_emoji, mod['pips'], sec['roll'], stat_value, stat_name))
		msgs.append({
			'title': '%d Roll Mods of %s' % (MIN_ROLLS, player_name),
			'description': '\n'.join(lines),
		})

	return msgs
