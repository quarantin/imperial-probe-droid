#!/usr/bin/python3

from opts import *
from utils import basicstrip, get_mod_sets_emojis, get_mod_primaries
from constants import EMOJIS, SHORT_STATS

from swgohgg import get_char_list, get_avatar_url, get_full_avatar_url
from swgohhelp import fetch_players, fetch_units

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
**`criticaldamange`** (or **`cd`**)
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
**`criticaldamange`** (or **`cd`**)
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

def cmd_wntm(config, author, channel, args):

	args, selected_filters = parse_opts_mod_filters(args)

	if args:
		plural = len(args) > 1
		return [{
			'title': 'Unknown Parameter%s' % plural,
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
		}]

	if not selected_filters:
		return [{
			'title': 'No Units Selected',
			'color': 'red',
			'description': 'You have to provide at least one unit name or a mod filter.\nPlease check %shelp recos for more information.' % config['prefix'],
		}]

	spacer = EMOJIS['']
	emoji_cg = EMOJIS['capitalgames']
	emoji_cr = EMOJIS['crouchingrancor']

	matching_recos = []
	for modset, slot, prim in selected_filters:
		for name, recos in sorted(config['recos']['by-name'].items()):
			for reco in recos:

				alist = [ reco[x] for x in range(3, 6) ]
				if modset not in [ reco[x] for x in range(3, 6) ]:
					continue

				if prim != reco[5 + slot]:
					continue

				matching_recos.append(reco)

	modset = EMOJIS[ modset.replace(' ', '').lower() ]
	slot = EMOJIS[ slot ]

	lines = []
	if not matching_recos:
		lines.append('No matching recommendation for the supplied mod filter.')
	else:
		chars = {}
		for recos in matching_recos:
			char_name = recos[0]
			if char_name.startswith('"'):
				char_name = char_name[1:]
			if char_name.endswith('"'):
				char_name = char_name[:-1]
			char_name = char_name.replace('""', '"')

			source = recos[1].replace(' ', '').lower()
			source_emoji = EMOJIS[source]
			if char_name not in chars:
				chars[char_name] = []

			if source_emoji not in chars[char_name]:
				chars[char_name].append(source_emoji)

		for charac, sources in sorted(chars.items()):
			if len(sources) < 2:
				if sources[0].startswith('<:cg:'):
					sources.append(spacer)
				else:
					sources.insert(0, spacer)

				lines.append('%s %s' % (''.join(sources), charac))

	return [{
		'author': {
			'name': 'Who Needs This Mod',
		},
		'title': '== %s%s %s ==' % (modset, slot, prim),
		'description': '\n'.join(lines),
		'fields': [
			{
				'name': '== Legend ==',
				'value': '\u202F%s EA / Capital Games\n\u202F%s Crouching Rancor\n%s' % (emoji_cg, emoji_cr, config['separator']),
				'inline': True,
			},
		]
	}]
