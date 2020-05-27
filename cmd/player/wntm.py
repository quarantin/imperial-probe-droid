from utils import get_field_legend
from constants import EMOJIS, MODSLOTS

import DJANGO
from swgoh.models import BaseUnit, ModRecommendation

help_wntm = {
	'title': 'Who Need This Mod Help',
	'description': """List characters who need mods with specific criteria (mod set, mod slot, and primary stat)

**Syntax**
```
%prefixwntm [mod filter]```
**Aliases**
```
%prefixw```
**Options**
The **`mod filter`** parameter must be of the form **`mod-set/mod-slot/primary-stat`**.

Here is the list of valid mod sets:
**`health`** (or **`he`**)
**`defense`** (or **`de`**)
**`potency`** (or **`po`**)
**`tenacity`** (or **`te`**)
**`criticalchance`** (or **`cc`**)
**`criticaldamage`** (or **`cd`**)
**`offense`** (or **`of`**)
**`speed`** (or **`sp`**)

Here is the list of valid mod slots:
**`square`** (or **`sq`**)
**`arrow`** (or **`ar`**)
**`diamond`** (or **`di`**)
**`triangle`** (or **`tr`**)
**`circle`** (or **`ci`**)
**`cross`** (or **`cr`**)

Here is the list of valid mod primary stats:
**`accuracy`** (or **`ac`**)
**`criticalavoidance`** (or **`ca`**)
**`criticalchance`** (or **`cc`**)
**`criticaldamage`** (or **`cd`**)
**`defense`** (or **`de`**)
**`health`** (or **`he`**)
**`offense`** (or **`of`**)
**`potency`** (or **`po`**)
**`protection`** (or **`pr`**)
**`speed`** (or **`sp`**)
**`tenacity`** (or **`te`**)

**Examples**
List characters who need a `defense` `arrow` mod with `speed` as primary stat:
```
%prefixw defense/arrow/speed```
Or the shorter form:
```
%prefixw de/ar/sp```"""
}

def cmd_wntm(ctx):

	bot = ctx.bot
	args = ctx.args
	config = ctx.config

	selected_filters = bot.options.parse_mod_filters(args)

	if args:
		return bot.errors.unknown_parameters(args)

	if not selected_filters:
		return bot.errors.no_mod_filter_selected(ctx)

	spacer = EMOJIS['']
	emoji_ea = EMOJIS['capitalgames']
	emoji_cr = EMOJIS['crouchingrancor']
	emoji_gg = EMOJIS['swgoh.gg']

	matching_recos = []
	recos = ModRecommendation.objects.all().values()
	for modset, slot, prim in selected_filters:
		for reco in recos:

			alist = [ reco['set1'], reco['set2'], reco['set3'] ]
			if modset not in alist:
				continue

			slot_name = MODSLOTS[slot].lower()
			if prim != reco[slot_name]:
				continue

			matching_recos.append(reco)

	modset = EMOJIS[ modset.replace(' ', '').lower() ]
	slot = EMOJIS[ slot ]

	lines = []
	if not matching_recos:
		lines.append('No matching recommendation for the supplied mod filter.')
	else:
		chars = {}
		for reco in matching_recos:
			unit = BaseUnit.objects.get(id=reco['character_id'])
			char_name = unit.name
			if char_name.startswith('"'):
				char_name = char_name[1:]
			if char_name.endswith('"'):
				char_name = char_name[:-1]
			char_name = char_name.replace('""', '"')

			source = reco['source'].replace(' ', '').lower()
			source_emoji = EMOJIS[source]
			if char_name not in chars:
				chars[char_name] = [ spacer, spacer, spacer ]

			if source_emoji not in chars[char_name]:

				if source_emoji.startswith('<:ea:'):
					chars[char_name][0] = source_emoji
				elif source_emoji.startswith('<:cr:'):
					chars[char_name][1] = source_emoji
				elif source_emoji.startswith('<:gg:'):
					chars[char_name][2] = source_emoji
				else:
					raise Exception('Unknown source')

		for charac, sources in sorted(chars.items()):
				lines.append('%s %s' % (''.join(sources), charac))

	return [{
		'author': {
			'name': '=== Who Need This Mod ==='
		},
		'title': '== %s%s %s ==' % (modset, slot, prim),
		'description': '\n'.join(lines),
		'fields': [
			get_field_legend(config),
		]
	}]
