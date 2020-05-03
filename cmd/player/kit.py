from opts import *
from errors import *
from utils import translate

from swgohgg import get_full_avatar_url
from swgohhelp import fetch_players, get_ability_name

import DJANGO
from swgoh.models import BaseUnitSkill

help_kit = {
	'title': 'Kit Help',
	'description': """Shows the ability kit of a given character or ship.

**Syntax**
```
%prefixkit [unit] [skill-type] [tier]```
**Aliases**
```
%prefixk```
**Options**
The `skill-type` option can be any of:
**`basic`**   or **`b`**: Show basic skills.
**`contract`** or **`c`**: Show contract skills.
**`hardware`** or **`h`**: Show hardware skills.
**`leader`**  or **`l`**: Show leader skills.
**`special`** or **`s`**: Show special skills.
**``** or **``**: Show skills.
The `tier` option can either be a number, or the special value `max`.
**Examples**
Show list of abilities for General Skywalker:
```
%prefixkit gas```
Show General skywalker leader ability:
```
%prefixkit gas leader```
Show General Skywalker second special ability:
```
%prefixkit gas special 2```"""
}

skill_types = {
	'b':        'basicability',
	'basic':    'basicability',
	'c':        'contractability',
	'contract': 'contractability',
	'h':        'hardwareability',
	'hw':       'hardwareability',
	'hardware': 'hardwareability',
	'l':        'leaderability',
	'leader':   'leaderability',
	's':        'specialability',
	'special':  'specialability',
	'u':        'uniqueability',
	'unique':   'uniqueability',
}

def parse_opts_tier(args):

	tier = None
	args_cpy = list(args)
	for arg in args_cpy:
		if arg.lower() == 'max':
			args.remove(arg)
			return 'max'

		try:
			tier = int(arg)
			args.remove(arg)
			break
		except:
			pass

	return tier

def parse_opts_skill_types(args):

	types = []
	args_cpy = list(args)
	for arg in args_cpy:
		larg = arg.lower()
		if larg in skill_types:
			skill_type = skill_types[larg]
			args.remove(arg)
			if skill_type not in types:
				types.append(skill_type)

	return types

def fix_desc(desc):

	colors = [
		'f0ff23',
		'ffff33',
		'F0FF23',
		'ffffff',
		'FFCC33',
		'FF0000',
		'B5E7F5',
		'FFA500',
		'e60000',
	]

	count = 0
	for color in colors:
		token = '[c][%s]' % color
		while token in desc:
			desc = desc.replace(token, '__**', 1)
			count += 1

	return desc.replace('\\n', '\n').replace('[-][/c]', '**__', count).replace('[-][/c]', '')

async def cmd_kit(request):

	args = request.args
	author = request.author
	config = request.config

	language = parse_opts_lang(request)

	selected_skill_types = parse_opts_skill_types(args)
	if not selected_skill_types:
		selected_skill_types = [ 'basicability', 'contractability', 'hardwareability', 'leaderability', 'specialability', 'uniqueability' ]

	selected_tier = parse_opts_tier(args)

	selected_players, error = parse_opts_players(request, min_allies=1, max_allies=1)

	selected_units = parse_opts_unit_names(request)

	if error:
		return error

	if not selected_players:
		return error_no_ally_code_specified(config, author)

	if not selected_units:
		return error_no_unit_selected()

	if args:
		return error_unknown_parameters(args)

	ally_codes = [ x.ally_code for x in selected_players ]
	players = await fetch_players(config, {
		'allycodes': ally_codes,
		'project': {
			'allyCode': 1,
			'name': 1,
			'roster': {
				'defId': 1,
				'gear': 1,
				'level': 1,
				'rarity': 1,
				'relic': 1,
				'skills': 1,
			},
		},
	})

	msgs = []
	for player in selected_players:

		jplayer = players[player.ally_code]

		for unit in selected_units:

			player_unit = unit.base_id in jplayer['roster'] and jplayer['roster'][unit.base_id] or None

			skills = BaseUnitSkill.objects.filter(unit=unit)
			for skill in skills:

				ability_type = skill.ability_ref.split('_')[0]
				if ability_type not in selected_skill_types:
					continue

				tier = selected_tier
				if not tier:
					if unit.base_id in players[player.ally_code]['roster']:
						unit_skills = players[player.ally_code]['roster'][unit.base_id]['skills']
						for unit_skill in unit_skills:
							if unit_skill['id'] == skill.skill_id and 'tier' in unit_skill:
								tier = unit_skill['tier']
								break
						else:
							tier = 1

				if not tier or tier == 'max' or tier > skill.max_tier:
					tier = skill.max_tier

				string_id = '%s_tier%02d' % (skill.ability_ref, tier)

				unit_name = translate(unit.base_id, language)
				skill_name = get_ability_name(skill.skill_id, language)
				skill_desc = fix_desc(translate(string_id, language))
				ability_type = ability_type.replace('ability', '').title()

				msgs.append({
					'title': unit_name,
					'thumbnail': {
						'url': get_full_avatar_url(config, unit, player_unit),
					},
					'description': '__**%s** (%s, %d/%d)__\n*%s*' % (skill_name, ability_type, tier, skill.max_tier, skill_desc),
					'image': {
						'url': 'http://zeroday.biz/skill/%s/' % skill.skill_id,
					},
					'no-sep': True,
				})

	if not msgs:
		units = '\n- '.join([ translate(unit.base_id, language) for unit in selected_units ])
		skill_types = ', or '.join([ x.replace('ability', '') for x in selected_skill_types ])
		plural = len(selected_units) > 1 and 's' or ''
		plural_have = len(selected_units) > 1 and 'have' or 'has'
		msgs.append({
			'title': 'No Matching Skills',
			'description': 'The following unit%s %s no %s skill%s:\n- %s' % (plural, plural_have, skill_types, plural, units),
		})

	return msgs
