#!/usr/bin/python3

from constants import EMOJIS, MODSETS_LIST

help_needed = {
	'title': '',
	'description': """Shows needed modsets according to recommendations.

**Syntax**
```
%prefixneeded [ally code]```

**Aliases**
```
%prefixn```

**Examples**
```
%prefixn
%prefixn 123456789```"""
}

def cmd_needed(config, author, channel, args):

	modsets = {}

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
					new_modsets[aset] = new_modsets[aset] + 1.0 / amount

		for aset, count in new_modsets.items():

			if aset not in modsets:
				modsets[aset] = {}

			if source not in modsets[aset]:
				modsets[aset][source] = 0.0

			modsets[aset][source] = modsets[aset][source] + count

	lines = []
	for aset in MODSETS_LIST:
		sources = modsets[aset]
		counts = []
		for source, count in sorted(sources.items()):
			modset_emoji = EMOJIS[ aset.replace(' ', '').lower() ]
			#source_emoji = EMOJIS[ source.replace(' ', '').lower() ]
			counts.append('x %.3g' % count)

		lines.append('%s `%s`' % (modset_emoji, ' | '.join(counts)))

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
		'description': '\n'.join(lines),
	}]
