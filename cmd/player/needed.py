from opts import *
from errors import *
from utils import roundup, get_field_legend
from constants import EMOJIS, MODSETS, MODSLOTS, MODSPRIMARIES

help_needed = {
	'title': 'Needed Help',
	'description': """Shows statistics about recommended mod sets and mod primaries according to EA / Capital Games, Crouching Rancor, and swgoh.gg's mod meta reports.

**Syntax**
```
%prefixneeded```
**Aliases**
```
%prefixn```
**Examples**
```
%prefixn```"""
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
	src_emojis = []
	for source in sources:
		emoji_key = source.replace(' ', '').lower()
		if emoji_key in EMOJIS:
			src_emojis.append(EMOJIS[emoji_key])

	headers = [ '%s%s' % (spacer, '|'.join(src_emojis)) ]

	for source, names in config['recos']['by-source'].items():

		new_modsets = {}
		for name, recos in names.items():

			amount = len(recos)
			for reco in recos:

				sets = [ reco['set1'], reco['set2'], reco['set3'] ]

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

			counts = []
			sources = modsets[aset_name]
			for source, count in sorted(sources.items()):
				modset_emoji = EMOJIS[ aset_name.replace(' ', '').lower() ]
				count = roundup(count)
				pad = pad_numbers(count)
				counts.append('%s%s' % (pad, count))

			if len(counts) < 3:
				pad = pad_numbers(0)
				counts.append('%s%d' % (pad, 0))

			lines.append('%s `%s`' % (modset_emoji, '|'.join(counts)))

	lines.append(config['separator'])

	lines = headers + lines

	return {
		'name': '== Needed Mod Sets ==',
		'value': '\n'.join(lines),
		'inline': True,
	}

def get_field_primary_stats(config, ally_codes, selected_slots, selected_primaries):

	spacer = EMOJIS['']

	if not selected_slots:
		selected_slots = MODSLOTS.values()

	if not selected_primaries:
		selected_primaries = MODSPRIMARIES

	lines = []
	stats = config['recos']['stats']
	for slot in selected_slots:
		slot = slot.lower()
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
		emoji_key = source.replace(' ', '').lower()
		if emoji_key in EMOJIS:
			emojis.append(EMOJIS[emoji_key])

	lines = [
		'%s\u202F\u202F\u202F%s`|Primary Stats`' % (spacer, '|'.join(emojis)),
	] + lines

	return '\n'.join(lines)

def cmd_needed(config, author, channel, args):

	args, players, error = parse_opts_players(config, author, args)
	args, selected_slots = parse_opts_modslots(args)
	args, selected_primaries = parse_opts_modprimaries(args)

	emoji_cg = EMOJIS['capitalgames']
	emoji_cr = EMOJIS['crouchingrancor']
	emoji_gg = EMOJIS['swgoh.gg']

	if args:
		return error_unknown_parameters(args)

	if error:
		return error

	ally_codes = [ player.ally_code for player in players ]
	field_primary_stats = get_field_primary_stats(config, ally_codes, selected_slots, selected_primaries)
	field_modset_stats  = get_field_modset_stats(config)
	field_legend        = get_field_legend(config)

	return [{
		'title': '== Needed Mod Primaries ==',
		'description': field_primary_stats,
		'fields': [
			field_modset_stats,
			field_legend,
		],
	}]
