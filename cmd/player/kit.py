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
				'skills': 1,
			},
		},
	})

	msgs = []
	for player in selected_players:
		for unit in selected_units:

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

				if not tier or tier == 'max':
					tier = (ability_type.startswith('hardware') or ability_type.startswith('contract')) and 3 or 8

				string_id = '%s_tier%02d' % (skill.ability_ref, tier)

				unit_name = translate(unit.base_id, language)
				skill_name = get_ability_name(skill.skill_id, language)
				skill_desc = fix_desc(translate(string_id, language))
				ability_type = ability_type.replace('ability', '').title()

				msgs.append({
					'title': unit_name,
					'thumbnail': {
						'url': 'http://zeroday.biz/avatar/%s' % unit.base_id,
					},
					'description': '__**%s** (%s)__\n*%s*' % (skill_name, ability_type, skill_desc),
					'image': {
						'url': 'http://zeroday.biz/skill/%s/' % skill.skill_id,
					},
					'no-sep': True,
				})

	return msgs
