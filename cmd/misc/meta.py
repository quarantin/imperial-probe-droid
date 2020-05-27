from swgohgg import get_top_rank1_squad_leaders, get_top_rank1_arena_squads, get_top_rank1_fleet_commanders, get_top_rank1_fleet_squads, get_top_rank1_reinforcements, META_UNITS_URL, META_SHIPS_URL

help_meta = {
	'title': 'Meta Help',
	'description': """Shows top squads from meta reports.

**Syntax**
```
%prefixmeta <option>... [n]```
**Options**
You have to supply one or more options:
**`leader`** or **`l`**: To show top leaders from meta reports.
**`commander`** or **`c`**: To show top commanders from meta reports.
**`arena`** or **`a`**: To show top arena squads from meta reports.
**`fleet`** or **`f`**: To show top fleet arena squads from meta reports.
**`reinforcements`** or **`r`**: To show top reinforcements from meta reports.
**`compact`** or **`C`**: (Optional) For compact display.
**`n`**: (Optional) A number. Get the top **`n`** squads (default is 5).

**Aliases**
```
%prefixm```
**Examples**
Show top 5 arena squads:
```
%prefixmeta a```
Show top 5 fleet arena squads:
```
%prefixmeta f```
Show top 3 arena squad leaders:
```
%prefixmeta l 3```
Show top 3 fleet arena commanders:
```
%prefixmeta c 3```
Show top 3 fleet reinforcements:
```
%prefixmeta r 3```"""
}

async def cmd_meta(ctx):

	bot = ctx.bot
	args = ctx.args
	config = ctx.config

	msgs = []
	selected_opts, top_n = bot.options.parse_meta(args)

	if args:
		plural = len(args) > 1 and 's' or ''
		return [{
				'title': 'Error: Invalid Parameter%s' % plural,
				'color': 'red',
				'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
			}]

	if not selected_opts:
		return [{
			'title': 'Error: Missing Option',
			'color': 'red',
			'description': 'I need at least one option. Please type `%shelp meta` to see available options.' % config['prefix'],
		}]


	compact = 'compact' in selected_opts
	sep = config['separator'].replace('`', '')
	header = '|---|-----|----------------'
	joke = 'joke' in config and config['joke'] is True

	if 'leader' in selected_opts:
		top_leaders = await get_top_rank1_squad_leaders(top_n)
		lines = []

		if joke:
			if compact:
				lines.append(sep)
				lines.append('88%')
				lines.append('7481')
				lines.append('Coruscant Underworld Police')
			else:

				pad1 = max(0, (3 - len('88%'))) * '\u00a0'
				pad2 = max(0, (5 - len('7481'))) * '\u00a0'
				lines.append('|%s%s|%s%s|%s' % (pad1, '88%', pad2, '7481', 'Coruscant Underworld Police'))

		for leader in top_leaders:
			unit, count, percent = leader
			if compact:
				lines.append(sep)
				lines.append(percent)
				lines.append(count)
				lines.append(unit)
			else:
				pad1 = max(0, (3 - len(percent))) * '\u00a0'
				pad2 = max(0, (5 - len(count))) * '\u00a0'
				lines.append('|%s%s|%s%s|%s' % (pad1, percent, pad2, count, unit))

		lines = lines[0:-1]
		desc = '' #'You can find the full meta report for top squad leaders [here](%s#leaders).' % META_UNITS_URL
		full_desc = '%s```| %% |Count|Unit\n%s\n%s```' % (desc, header, '\n'.join(lines))
		compact_desc = '%s```%s```' % (desc, '\n'.join(lines))

		msgs.append({
			'title': 'Top %d - Arena Squad Leaders' % top_n,
			'author': {
				'icon_url': '%s/media/imperial-probe-droid.jpg' % config.get_server_url(),
			},
			'description': compact and compact_desc or full_desc,
		})

	if 'arena' in selected_opts:
		top_squads = await get_top_rank1_arena_squads(top_n)
		lines = []

		if joke:
			squad = [
				'Clone Wars Chewbacca',
				'Coruscant Underworld Police',
				'Mob Enforcer',
				'Jedi Knight Guardian',
				'Jedi Consular',
			]

			if compact:
				lines.append(sep)
				lines.append('88%')
				lines.append('7481')
				lines.append('---')
				for unit in squad:
					lines.append(unit)
			else:

				pad1 = max(0, (3 - len('88%'))) * '\u00a0'
				pad2 = max(0, (5 - len('7481'))) * '\u00a0'
				lines.append('|%s|%s|%s' % (pad1, '88%', pad2, '7481', squad[0]))
				for unit in squad[1:]:
					lines.append('|   |     |%s' % unit)
				lines.append(header)

		for tupl in top_squads:
			squad, count, percent = tupl
			if compact:
				lines.append(sep)
				lines.append(percent)
				lines.append(count)
				lines.append('---')
				for unit in squad:
					lines.append(unit)
			else:
				pad1 = max(0, (3 - len(percent))) * '\u00a0'
				pad2 = max(0, (5 - len(count))) * '\u00a0'
				lines.append('|%s%s|%s%s|%s' % (pad1, percent, pad2, count, squad[0]))
				for unit in squad[1:]:
					lines.append('|   |     |%s' % unit)
				lines.append(header)

		lines = lines[0:-1]
		desc = '' #'You can find the full meta report for top arena squads [here](%s#squads).' % META_UNITS_URL
		full_desc = '%s```| %% |Count|Squad\n%s\n%s```' % (desc, header, '\n'.join(lines))
		compact_desc = '%s```%s```' % (desc, '\n'.join(lines))

		msgs.append({
			'title': 'Top %d - Arena Squads ' % top_n,
			'author': {
				'icon_url': '%s/media/imperial-probe-droid.jpg' % config.get_server_url(),
			},
			'description': compact and compact_desc or full_desc,
		})

	if 'commander' in selected_opts:
		top_commanders = await get_top_rank1_fleet_commanders(top_n)
		lines = []

		for commander in top_commanders:
			unit, count, percent = commander
			if compact:
				lines.append(sep)
				lines.append(percent)
				lines.append(count)
				lines.append(unit)
			else:
				pad1 = max(0, (3 - len(percent))) * '\u00a0'
				pad2 = max(0, (5 - len(count))) * '\u00a0'
				lines.append('|%s%s|%s%s|%s' % (pad1, percent, pad2, count, unit))

		lines = lines[0:-1]
		desc = '' #'You can find the full meta report for top fleet commanders [here](%s#leaders).' % META_SHIPS_URL
		full_desc = '%s```\n| %% |Count|Unit\n%s\n%s```' % (desc, header, '\n'.join(lines))
		compact_desc = '%s```%s```' % (desc, '\n'.join(lines))

		msgs.append({
			'title': 'Top %d - Fleet Arena Commanders' % top_n,
			'author': {
				'icon_url': '%s/media/imperial-probe-droid.jpg' % config.get_server_url(),
			},
			'description': compact and compact_desc or full_desc,
		})

	if 'fleet' in selected_opts:
		top_squads = await get_top_rank1_fleet_squads(top_n)
		lines = []

		for tupl in top_squads:
			squad, count, percent = tupl
			if compact:
				lines.append(sep)
				lines.append(percent)
				lines.append(count)
				lines.append('---')
				for unit in squad:
					lines.append(unit)
			else:
				pad1 = max(0, (3 - len(percent))) * '\u00a0'
				pad2 = max(0, (5 - len(count))) * '\u00a0'
				lines.append('|%s%s|%s%s|%s' % (pad1, percent, pad2, count, squad[0]))
				for unit in squad[1:]:
					lines.append('|   |     |%s' % unit)
				lines.append(header)

		lines = lines[0:-1]
		desc = '' #'You can find the full meta report for top fleet arena squads [here](%s#squads).' % META_SHIPS_URL
		full_desc = '%s```| %% |Count|Squad\n%s\n%s```' % (desc, header, '\n'.join(lines))
		compact_desc = '%s```%s```' % (desc, '\n'.join(lines))

		msgs.append({
			'title': 'Top %d - Fleet Arena Squads ' % top_n,
			'author': {
				'icon_url': '%s/media/imperial-probe-droid.jpg' % config.get_server_url(),
			},
			'description': compact and compact_desc or full_desc,
		})

	if 'reinforcement' in selected_opts:
		top_reinforcements = await get_top_rank1_reinforcements(top_n)
		lines = []

		for tupl in top_reinforcements:
			squad, count, percent = tupl
			if compact:
				lines.append(sep)
				lines.append(percent)
				lines.append(count)
				for unit in squad:
					lines.append(unit)
			else:
				pad1 = max(0, (3 - len(percent))) * '\u00a0'
				pad2 = max(0, (5 - len(count))) * '\u00a0'
				lines.append('|%s%s|%s%s|%s' % (pad1, percent, pad2, count, squad[0]))
				for unit in squad[1:]:
					lines.append('|   |     |%s' % unit)
				lines.append(header)

		lines = lines[0:-1]
		desc = '' #'You can find the full meta report for top fleet arena reinforcements [here](%s#reinforcements).' % META_SHIPS_URL
		full_desc = '%s```| %% |Count|Ship\n%s\n%s```' % (desc, header, '\n'.join(lines))
		compact_desc = '%s```%s```' % (desc, '\n'.join(lines))

		msgs.append({
			'title': 'Top %d - Fleet Arena Reinforcements' % top_n,
			'author': {
				'icon_url': '%s/media/imperial-probe-droid.jpg' % config.get_server_url(),
			},
			'description': compact and compact_desc or full_desc,
		})


	return msgs
