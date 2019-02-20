#!/usr/bin/python3

from utils import roundup, get_field_legend
from opts import parse_opts_ally_codes, parse_opts_modslots, parse_opts_modprimaries
from constants import EMOJIS, MODSETS, MODSETS_LIST, MODSLOTS, MODSPRIMARIES, SHORT_STATS

help_needed = {
	'title': 'Needed Help',
	'description': """Shows statistics about recommended mod sets and mod primaries according to Capital Games and Crouching Rancor.

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

def pad_numbers(number):

	pad = '\u202F'

	if number < 10:
		return pad * 4

	if number < 100:
		return pad * 2

	return ''

def get_field_modset_stats(config):

	modsets = {}
	spacer = EMOJIS['']
	sources = sorted(list(config['recos']['by-source']))
	src_emojis = [ spacer ]
	for source in sources:
		emoji = EMOJIS[ source.replace(' ', '').lower() ]
		src_emojis.append(spacer)
		src_emojis.append(emoji)

	headers = [ ''.join(src_emojis) ]

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

		lines = []
		for aset, count in new_modsets.items():

			if aset not in modsets:
				modsets[aset] = {}

			if source not in modsets[aset]:
				modsets[aset][source] = 0.0

			modsets[aset][source] += count

		for aset_name in MODSETS.values():
			if aset_name not in modsets:
				continue

			sources = modsets[aset_name]
			counts = []
			for source, count in sorted(sources.items()):
				modset_emoji = EMOJIS[ aset_name.replace(' ', '').lower() ]
				counts.append('x %.3g' % count)

			lines.append('%s `%s`' % (modset_emoji, ' | '.join(counts)))

	lines.append(config['separator'])

	lines = headers + lines

	return {
		'name': '== Needed Mod Sets ==',
		'value': '\n'.join(lines),
		'inline': True,
	}

def get_field_primary_stats(config, ally_codes, selected_slots, selected_primaries):

	if not selected_slots:
		selected_slots = MODSLOTS.keys()

	if not selected_primaries:
		selected_primaries = MODSPRIMARIES

	#for ally_code in ally_codes:

	#ally_stats = get_mod_stats(ally_code)

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
				if 'Capital Games' in stats[slot][primary]:
					cg_count = roundup(stats[slot][primary]['Capital Games'])

				cr_count = 0.0
				if 'Crouching Rancor' in stats[slot][primary]:
					cr_count = roundup(stats[slot][primary]['Crouching Rancor'])

				gg_count = 0.0
				if 'swgoh.gg' in stats[slot][primary]:
					gg_count = roundup(stats[slot][primary]['swgoh.gg'])

				ally_count = 0.0
				#if slot in ally_stats and primary in ally_stats[slot]:
				#	ally_count = roundup(ally_stats[slot][primary])

				pad1 = pad_numbers(cg_count)
				pad2 = pad_numbers(cr_count)
				pad3 = pad_numbers(gg_count)
				pad4 = pad_numbers(ally_count)

				sublines.append('%s `|%s%.3g|%s%.3g|%s%.3g|%s%.3g|%s`' % (slot_emoji, pad1, cg_count, pad2, cr_count, pad3, gg_count, pad4, ally_count, primary))

		if sublines:
			lines += [ config['separator'] ] + sublines

	sources = sorted(list(config['recos']['by-source'])) + [ 'crimsondeathwatch' ]
	emojis = []
	for source in sources:
		emoji = EMOJIS[ source.replace(' ', '').lower() ]
		emojis.append(emoji)

	lines = [
		'`Slot|`%s`|Primary Stats`' % '|'.join(emojis),
	] + lines

	return '\n'.join(lines)

def cmd_needed(config, author, channel, args):

	args, ally_codes = parse_opts_ally_codes(config, author, args)
	args, selected_slots = parse_opts_modslots(args)
	args, selected_primaries = parse_opts_modprimaries(args)


	emoji_cg = EMOJIS['capitalgames']
	emoji_cr = EMOJIS['crouchingrancor']
	emoji_gg = EMOJIS['swgoh.gg']

	if args:
		plural = len(args) > 1 and 's' or ''
		return [{
			'title': 'Unknown Parameter%s' % plural,
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % '\n - '.join(args),
		}]

	field_modset_stats  = get_field_modset_stats(config)
	field_primary_stats = get_field_primary_stats(config, ally_codes, selected_slots, selected_primaries)
	field_legend        = get_field_legend(config)

	return [{
		'title': '== Needed Mod Primaries ==',
		'description': field_primary_stats,
		'fields': [
			field_modset_stats,
			field_legend,
		],
	}]
