#!/usr/bin/python3

import re

from opts import *
from swgoh import get_my_mods, get_player_name
from constants import EMOJIS, MODSETS, MODSETS_LIST, MODSETS_NEEDED, MODSLOTS

help_stats = {
	'title': 'Player info',
	'description': """Shows statistics about equipped mods for the supplied ally codes.

**Syntax**
```
%prefixstats [ally codes]
%prefixstats [ally codes] [shapes]
%prefixstats [ally codes] [modsets]
%prefixstats [ally codes] [modsets] [shapes]```

**Aliases**
```
%prefixs```

**Modsets**
Modset parameters can be any of:
```
health (or he)
defense (or de)
potency (or po)
tenacity (or te)
critical-chance (or cc)
critical-damage (or cd)
offense (or of)
speed (or sp)```

**Mod shapes**
Mod shape parameters can be any of:
```
square (or sq)
arrow (or ar)
diamond (or di)
triangle (or tr)
circle (or ci)
cross (or cr)```

**Examples**
```
%prefixs
%prefixs 123456789
%prefixs speed
%prefixs cd tr
%prefixs speed arrow
%prefixs 123456789 speed arrow```"""
}

def atoi(text):
	return int(text) if text.isdigit() else text

def natural_keys(text):
	'''
	alist.sort(key=natural_keys) sorts in human order
	http://nedbatchelder.com/blog/200712/human_sorting.html
	(See Toothy's implementation in the comments)
	'''
	return [ atoi(c) for c in re.split('(\d+)', text) ]

def count_mods_per_shape(mod_shapes):

	shape_count = {}

	for modset, shapes in mod_shapes.items():
		for shape, count in shapes.items():
			if shape not in shape_count:
				shape_count[shape] = 0

			shape_count[shape] = shape_count[shape] + count

	return shape_count

def parse_mod_counts(mods):

	count = {}
	shapes = {}
	primaries = {}

	for mod in mods:

		modset_id = mod['set']
		modset = MODSETS[modset_id]
		if modset_id not in count:
			count[modset_id] = 0
			shapes[modset_id] = {}
			primaries[modset_id] = {}
		count[modset_id] += 1

		shape_id = mod['slot']
		shape_name = MODSLOTS[shape_id]
		if shape_id not in shapes[modset_id]:
			shapes[modset_id][shape_id] = 0
			primaries[modset_id][shape_id] = {}
		shapes[modset_id][shape_id] += 1

		primary = mod['primary_stat']['name']
		if primary not in primaries[modset_id][shape_id]:
			primaries[modset_id][shape_id][primary] = 0
		primaries[modset_id][shape_id][primary] += 1

	return count, shapes, primaries

def cmd_stats(config, author, channel, args):

	args, ally_codes = parse_opts_ally_codes(config, author, args)

	args, selected_modsets = parse_opts_modsets(args)

	args, selected_modshapes = parse_opts_modslots(args)

	if args:
		return [{
			'title': 'Unknown parameter(s)',
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter(s):\n - %s' % '\n - '.join(args),
		}]

	msgs = []
	for ally_code in ally_codes:

		ally_db = get_my_mods(ally_code)

		counts, shapes, primaries = parse_mod_counts(ally_db['mods'])

		player = get_player_name(ally_code)
		equipped_mods = ally_db['mods-count']

		if not selected_modsets and not selected_modshapes:

			lines = []

			shape_count = ally_db['mods-slots']
			for shape_id, shape_name in MODSLOTS.items():
				if shape_id in shape_count:
					count = shape_count[shape_id]
					emoji = EMOJIS[shape_name.replace(' ', '').lower()]
					lines.append('%s x %d mods' % (emoji, count))

			lines.append(config['separator'])

			for modset_id in MODSETS_LIST:
				modset_name = MODSETS[modset_id]
				count = counts[modset_id]
				emoji = EMOJIS[modset_name.replace(' ', '').lower()]
				modset_group = MODSETS_NEEDED[modset_id]
				modsets, remainder = divmod(count, modset_group)
				remain = remainder > 0 and ' + %d mod(s)' % remainder or ''
				pad1 = ''
				if count < 100:
					pad1 = u'\u202F\u202F'
				if count < 10:
					pad1 = pad1 * 2

				pad2 = ''
				if modsets < 100:
					pad2 = u'\u202F\u202F'
				if modsets < 10:
					pad2 = pad2 * 2

				lines.append('%s `x %s%d mods = %s%d modsets%s`' % (emoji, pad1, count, pad2, modsets, remain))

			msgs.append({
				'title': '%s Mods Statistics' % player,
				'description': 'Equipped mods: **%d**\n%s\n%s' % (equipped_mods, config['separator'], '\n'.join(lines)),
			})

		elif selected_modsets and not selected_modshapes:

			for modset_id in selected_modsets:

				lines = []
				total_for_modset = 0
				for shape_id, shape_name in MODSLOTS.items():
					if modset_id in shapes and shape_id in shapes[modset_id]:
						modset_name = MODSETS[modset_id]
						shape_name = MODSLOTS[shape_id]
						modset_emoji = EMOJIS[modset_name.replace(' ', '').lower()]
						modshape_emoji = EMOJIS[shape_name.replace(' ', '').lower()]
						count = shapes[modset_id][shape_id]
						pad = ''
						if count < 100:
							pad = u'\u202F\u202F'
						if count < 10:
							pad = pad * 2

						total_for_modset = total_for_modset + count

						line = '%s%s `x %s%d`' % (modset_emoji, modshape_emoji, pad, shapes[modset_id][shape_id])
						lines.append(line)

				modset_name = MODSETS[modset_id]
				msgs.append({
					'title': '%s %s Mods Statistics' % (player, modset_name),
					'description': 'Equipped %s mods: **%d**\n%s\n%s' % (modset_name.lower(), total_for_modset, config['separator'], '\n'.join(lines)),
				})

		elif not selected_modsets and selected_modshapes:

			pad = '\u202f' * 4
			lines = []
			total_for_modset = 0
			for modset_id in MODSETS_LIST:
				modset_name = MODSETS[modset_id]
				for shape_id in selected_modshapes:

					total_for_slot = 0
					shape_name = MODSLOTS[shape_id]
					modset_emoji = EMOJIS[modset_name.replace(' ', '').lower()]
					modshape_emoji = EMOJIS[shape_name.replace(' ', '').lower()]

					sublines = []
					desc = 'Equipped %s %s mods' % (modset_emoji, modshape_emoji)
					for primary, count in sorted(primaries[modset_id][shape_id].items()):
						total_for_slot += count
						total_for_modset += count
						sublines.append('%s`%d x %s`' % (pad, count, primary))

					sublines.sort(key=natural_keys)

					desc = '%s %s x %d' % (modset_emoji, modshape_emoji, total_for_modset)

					lines.append(desc)
					lines = lines + [ x for x in reversed(sublines) ]


			msgs.append({
				'title': '%s Mods Statistics' % player,
				'description': 'Equipped %s mods: **%d**\n%s\n%s' % (shape_name.lower(), total_for_modset, config['separator'], '\n'.join(lines)),
			})

		else:

			total_for_shape = 0
			for modset_id in selected_modsets:
				modset = MODSETS[modset_id]
				for shape_id in selected_modshapes:
					shape = MODSLOTS[shape_id]

					lines = []

					modset_emoji = EMOJIS[modset.replace(' ', '').lower()]
					modshape_emoji = EMOJIS[shape.replace(' ', '').lower()]
					for primary, count in primaries[modset_id][shape_id].items():
						pad = ''
						if count < 100:
							pad = u'\u202F\u202F'
						if count < 10:
							pad = pad * 2

						total_for_shape = total_for_shape + count
						line = '`%d x %s`' % (count, primary)
						lines.append(line)

					modset_name = MODSETS[modset_id]
					shape_name = MODSLOTS[shape_id]

					modset_emoji = EMOJIS[modset_name.replace(' ', '').lower()]
					shape_emoji = EMOJIS[shape_name.replace(' ', '').lower()]

					lines.sort(key=natural_keys)

					msgs.append({
						'title': '%s %s %s Mods Primaries' % (player, modset_name, shape_name),
						'description': 'Equipped %s %s mods: **%d**\n%s\n%s' % (modset_emoji, shape_emoji, total_for_shape, config['separator'], '\n'.join(reversed(lines))),
					})

	return msgs
