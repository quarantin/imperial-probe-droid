import re

from constants import EMOJIS
from swgohgg import get_full_avatar_url
from utils import translate, get_ability_name

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

def get_emoji(skill, tier):

	if skill.is_zeta:
		emoji = skill.max_tier == tier and 'zeta' or 'zetadisabled'

	elif skill.max_tier != 3:
		emoji = skill.max_tier == tier and 'omega' or 'omegadisabled'

	else:
		return ''

	return EMOJIS[emoji]

async def cmd_kit(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	config = ctx.config

	ctx.alt = bot.options.parse_alt(args)
	language = bot.options.parse_lang(ctx, args)

	selected_skill_types = bot.options.parse_skill_types(args)

	selected_tier = bot.options.parse_tier(args)

	selected_players, error = bot.options.parse_players(ctx, args, min_allies=1, max_allies=1)

	selected_units = bot.options.parse_unit_names(args)

	if error:
		return error

	if args:
		return bot.errors.unknown_parameters(args)

	if not selected_players:
		return bot.errors.no_ally_code_specified(ctx)

	if not selected_units:
		return bot.errors.no_unit_selected(ctx)

	ally_codes = [ x.ally_code for x in selected_players ]
	players = await bot.client.players(ally_codes=ally_codes)
	if not players:
		return bot.errors.ally_codes_not_found(ally_codes)

	players = { x['allyCode']: x for x in players }

	msgs = []
	for player in selected_players:

		jplayer = players[player.ally_code]
		jroster = { x['defId']: x for x in jplayer['roster'] }

		for unit in selected_units:

			player_unit = unit.base_id in jroster and jroster[unit.base_id] or None

			skills = BaseUnitSkill.objects.filter(unit=unit)
			for skill in skills:

				ability_type = skill.ability_ref.split('_')[0]
				if ability_type not in selected_skill_types:
					continue

				skill_index = selected_skill_types[ability_type]
				ends_with_index = re.search(r'0[0-9]$', skill.ability_ref)
				if ends_with_index:

					if skill_index != -1 and not skill.ability_ref.endswith('%02d' % skill_index):
						continue

				elif skill_index not in [ -1, 1 ]:
					continue

				tier = selected_tier
				if not tier:
					if unit.base_id in jroster:
						unit_skills = jroster[unit.base_id]['skills']
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

				emoji = get_emoji(skill, tier)

				msgs.append({
					'title': unit_name,
					'thumbnail': {
						'url': get_full_avatar_url(config, unit, player_unit),
					},
					'description': '%s __**%s** (%s, %d/%d)__\n*%s*' % (emoji, skill_name, ability_type, tier, skill.max_tier, skill_desc),
					'image': {
						'url': 'http://zeroday.biz/skill/%s/' % skill.skill_id,
					},
					'no-sep': True,
				})

	if not msgs:
		units = '\n- '.join([ translate(unit.base_id, language) for unit in selected_units ])
		plural_units = len(selected_units) > 1 and 's' or ''
		plural_skills = len(selected_skill_types) > 1 and 'ies' or 'y'
		msgs.append({
			'title': 'No Matching Skills',
			'description': 'Could not find matching abilit%s for the following unit%s:\n- %s' % (plural_skills, plural_units, units),
		})

	return msgs
