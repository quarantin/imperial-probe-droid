#!/usr/bin/python3

from opts import parse_opts_modslots, parse_opts_modprimaries
from constants import EMOJIS, MODSETS, MODSETS_LIST, MODSLOTS, MODSPRIMARIES

help_needed = {
	'title': '',
	'description': """Shows recommended mod sets and mod primaries according to Capital Games and Crouching Rancor.

**Syntax**
```
%prefixneeded [options]
%prefixneeded [mod slots] [mod primaries]```

**Aliases**
```
%prefixn```

**Options**
Valid options are as follow:
**`modsets`** (or **`m`**): to show stats about recommended mod sets.

**Mod Slots**
Mod slots parameters can be any of:
 - **`square`** (or **`sq`**)
 - **`arrow`** (or **`ar`**)
 - **`diamond`** (or **`di`**)
 - **`triangle`** (or **`tr`**)
 - **`circle`** (or **`ci`**)
 - **`cross`** (or **`cr`**)

**Mod Primaries**
Mod primaries parameters can be any of:
 - **`accuracy`** (or **`ac`**)
 - **`criticalavoidance`** (or **`ca`**)
 - **`criticalchance`** (or **`cc`**)
 - **`criticaldamage`** (or **`cd`**)
 - **`defense`** (or **`de`**)
 - **`health`** (or **`he`**)
 - **`offense`** (or **`of`**)
 - **`potency`** (or **`po`**)
 - **`protection`** (or **`pr`**)
 - **`speed`** (or **`sp`**)
 - **`tenacity`** (or **`te`**)

**Examples**
Show how many mods are recommended for all slots and primary stats:
```
%prefixn```
Show how many mod sets are recommended for each mod set:
```
%prefixn m```
Show how many mods are recommended with speed as primary stat:
```
%prefixn speed```
Show how many cross mods are recommended for each primary stat:
```
%prefixn cross```
Show how many arrow mods are recommended with speed as primary stat:
```
%prefixn arrow speed```
Show how many triangle mods are recommended with critical damage as primary stat:
```
%prefixn tr cd```"""
}

def cmd_needed(config, author, channel, args):

	msgs = []
	modsets = {}
	option = None

	args, selected_slots = parse_opts_modslots(args)
	args, selected_primaries = parse_opts_modprimaries(args)

	for arg in list(args):
		if arg in [ 'm', 'modsets' ]:
			args.remove(arg)
			option = 'modsets'

	if args:
		plural = len(args) > 1 and 's' or ''
		return [{
			'title': 'Unknown Parameter%s' % plural,
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % '\n - '.join(args),
		}]

	for source, names in config['recos']['by-source'].items():

		new_modsets = {}
		for name, recos in names.items():
			amount = len(recos)
			for reco in recos:

				sets = []

				sets.append(reco[3])
				sets.append(reco[4])
				if reco[5]:
					sets.append(reco[5])

				for aset in sets:
					if aset not in new_modsets:
						new_modsets[aset] = 0.0
					new_modsets[aset] += 1.0 / amount

		for aset, count in new_modsets.items():

			if aset not in modsets:
				modsets[aset] = {}

			if source not in modsets[aset]:
				modsets[aset][source] = 0.0

			modsets[aset][source] += count

		lines = []
		for aset in MODSETS.values():
			sources = modsets[aset]
			counts = []
			for source, count in sorted(sources.items()):
				modset_emoji = EMOJIS[ aset.replace(' ', '').lower() ]
				#source_emoji = EMOJIS[ source.replace(' ', '').lower() ]
				counts.append('x %.3g' % count)

			lines.append('%s `%s`' % (modset_emoji, ' | '.join(counts)))

	if option == 'modsets':

		sources = sorted(list(config['recos']['by-source']))
		src_emojis = []
		spacer = EMOJIS['']
		for source in sources:
			emoji = EMOJIS[ source.replace(' ', '').lower() ]
			src_emojis.append(spacer)
			src_emojis.append(emoji)

		emojis = ''.join(src_emojis)
		lines = [ emojis ] + lines

		return [{
			'title': 'Modsets needed',
			'description': '%s\n%s' % (config['separator'], '\n'.join(lines)),
		}]

	if not selected_slots:
		selected_slots = MODSLOTS.keys()

	if not selected_primaries:
		selected_primaries = MODSPRIMARIES

	lines = []
	stats = config['recos']['stats']
	for slot in selected_slots:
		slot_emoji = EMOJIS[slot]
		if slot not in stats:
			continue

		sublines = []
		for primary in sorted(selected_primaries):
			if primary in stats[slot]:
				cg_count = 0.0
				print(stats[slot][primary])
				if 'Capital Games' in stats[slot][primary]:
					cg_count = stats[slot][primary]['Capital Games']

				cr_count = 0.0
				if 'Crouching Rancor' in stats[slot][primary]:
					cr_count = stats[slot][primary]['Crouching Rancor']

				sublines.append('%s %s `x %.3g | x %.3g`' % (slot_emoji, primary, cg_count, cr_count))

		if sublines:
			lines += [ config['separator'] ] + sublines

	sources = sorted(list(config['recos']['by-source']))
	src_emojis = []
	spacer = EMOJIS['']
	for source in sources:
		emoji = EMOJIS[ source.replace(' ', '').lower() ]
		src_emojis.append(spacer)
		src_emojis.append(emoji)

	emojis = ''.join(src_emojis)

	msgs.append({
		'title': 'Recommended Mods Primaries',
		'description': '\n'.join([ emojis ] + lines),
	})

	return msgs
