#!/usr/bin/python3

from opts import *
from swgoh import *
from utils import lpad

help_meta = {
	'title': 'Meta Info',
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
**`n`**: (Optional) A number. Get the top **`n`** squads (default is 10).

**Aliases**
```
%prefixM```
**Examples**
Show top 5 arena squads:
```
%prefixM a```
Show top 5 fleet arena squads:
```
%prefixM f```
Show top 3 arena squad leaders:
```
%prefixM l 3```

Show top 3 fleet arena commanders:
```
%prefixM c 3```
Show top 3 fleet reinforcements:
```
%prefixM r 3"```"""
}

opts = {
	'a':             'arena',
	'arena':         'arena',
	'f':             'fleet',
	'fleet':         'fleet',
	'l':             'leader',
	'leader':        'leader',
	'c':             'commander',
	'commander':     'commander',
	'C':             'compact',
	'compact':       'compact',
	'r':             'reinforcement',
	'reinforcement': 'reinforcement',

}

def opts_meta(args):

	top_n = 5
	selected_opts = []
	args_cpy = list(args)

	for arg in args_cpy:

		if arg in opts:
			opt = opts[arg]
			args.remove(arg)
			selected_opts.append(opt)

		elif arg.isdigit():
			args.remove(arg)
			arg = int(arg)
			if arg < 1:
				arg = 1
			if arg > 50:
				arg = 50

			top_n = int(arg)

	return args, selected_opts, top_n
			
def cmd_meta(config, author, channel, args):

	msgs = []
	args, selected_opts, top_n = opts_meta(args)
	if args:
		plural = len(args) > 1 and 's' or ''
		return [{
				'title': 'Invalid Parameter%s' % plural,
				'color': 'red',
				'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
			}]

	if not selected_opts:
		return [{
			'title': 'Missing Option',
			'color': 'red',
			'description': 'I need at least one option. Please see `%shelp meta` to see available options.' % config['prefix'],
		}]


	compact = 'compact' in selected_opts
	sep = config['separator'].replace('`', '')
	header = '|---|-----|---------------------------'
	joke = 'joke' in config and config['joke'] is True

	if 'leader' in selected_opts:
		top_leaders = get_top_rank1_squad_leaders(top_n)
		lines = []

		if compact:
			lines.append(sep)
			lines.append('88%')
			lines.append('7481')
			lines.append('Coruscant Underworld Police')
		else:
			lines.append('|%s|%s|%s' % (lpad('88%', 10), lpad('7481', 10000), 'Coruscant Underworld Police'))

		for leader in top_leaders:
			unit, count, percent = leader
			if compact:
				lines.append(sep)
				lines.append(percent)
				lines.append(count)
				lines.append(unit)
			else:
				lines.append('|%s|%s|%s' % (lpad(percent, 10), lpad(count, 10000), unit))

		desc = 'You can find the full meta report for top squad leaders at this address:\n%s#leaders' % META_UNITS_URL
		full_desc = '%s\n```\n| %% |Count|Unit\n%s\n%s```' % (desc, header, '\n'.join(lines))
		compact_desc = '%s\n```\n%%\nCount\nUnit\n%s```' % (desc, '\n'.join(lines))

		msgs.append({
			'title': 'Top %d - Arena Squad Leaders' % top_n,
			'author': {
				'name': 'Imperial Probe Droid',
				'icon_url': 'http://zeroday.biz/media/imperial-probe-droid.jpg',
			},
			'description': compact and compact_desc or full_desc,
		})

	if 'commander' in selected_opts:
		top_commanders = get_top_rank1_fleet_commanders(top_n)
		lines = []

		for commander in top_commanders:
			unit, count, percent = commander
			if compact:
				lines.append(sep)
				lines.append(percent)
				lines.append(count)
				lines.append(unit)
			else:
				lines.append('|%s|%s|%s' % (lpad(percent, 10), lpad(count, 10000), unit))

		desc = 'You can find the full meta report for top fleet commanders at this address:\n%s#leeaders' % META_SHIPS_URL
		full_desc = '%s\n```\n| %% |Count|Unit\n|---|-----|---------------------------\n%s```' % (desc, '\n'.join(lines))
		compact_desc = '%s\n```\n%%\nCount\nUnit\n%s```' % (desc, '\n'.join(lines))

		msgs.append({
			'title': 'Top %d - Fleet Arena Commanders' % top_n,
			'author': {
				'name': 'Imperial Probe Droid',
				'icon_url': 'http://zeroday.biz/media/imperial-probe-droid.jpg',
			},
			'description': compact and compact_desc or full_desc,
		})

	if 'arena' in selected_opts:
		top_squads = get_top_rank1_arena_squads(top_n)
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
				lines.append('|%s|%s|%s' % (lpad('88%', 10), lpad('7481', 10000), squad[0]))
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
				lines.append('|%s|%s|%s' % (lpad(percent, 10), lpad(count, 10000), squad[0]))
				for unit in squad[1:]:
					lines.append('|   |     |%s' % unit)
				lines.append(header)

		desc = 'You can find the full meta report for top arena squads at this address:\n%s#squads' % META_UNITS_URL
		full_desc = '%s\n```\n| %% |Count|Squad\n%s\n%s```' % (desc, header, '\n'.join(lines))
		compact_desc = '%s\n```\n%%\nCount\n---\nSquad\n%s```' % (desc, '\n'.join(lines))

		msgs.append({
			'title': 'Top %d - Arena Squads ' % top_n,
			'author': {
				'name': 'Imperial Probe Droid',
				'icon_url': 'http://zeroday.biz/media/imperial-probe-droid.jpg',
			},
			'description': compact and compact_desc or full_desc,
		})

	if 'fleet' in selected_opts:
		top_squads = get_top_rank1_fleet_squads(top_n)
		lines = []

		if joke:
			squad = [
			]

			if compact:
				lines.append(sep)
				lines.append('88%')
				lines.append('7481')
				lines.append('---')
				for unit in squad:
					lines.append(unit)
			else:
				lines.append('|%s|%s|%s' % (lpad('88%', 10), lpad('7481', 10000), squad[0]))
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
				lines.append('|%s|%s|%s' % (lpad(percent, 10), lpad(count, 10000), squad[0]))
				for unit in squad[1:]:
					lines.append('|   |     |%s' % unit)
				lines.append(header)

		desc = 'You can find the full meta report for top fleet arena squads at this address:\n%s#squads' % META_SHIPS_URL
		full_desc = '%s\n```\n| %% |Count|Squad\n%s\n%s```' % (desc, header, '\n'.join(lines))
		compact_desc = '%s\n```\n%%\nCount\n---\nSquad\n%s```' % (desc, '\n'.join(lines))

		msgs.append({
			'title': 'Top %d - Fleet Arena Squads ' % top_n,
			'author': {
				'name': 'Imperial Probe Droid',
				'icon_url': 'http://zeroday.biz/media/imperial-probe-droid.jpg',
			},
			'description': compact and compact_desc or full_desc,
		})

	if 'reinforcement' in selected_opts:
		top_reinforcements = get_top_rank1_reinforcements(top_n)
		lines = []

		if joke:
			squad = [
			]

			if compact:
				lines.append(sep)
				lines.append('88%')
				lines.append('7481')
				for unit in squad:
					lines.append(unit)
			else:
				lines.append('|%s|%s|%s' % (lpad('88%', 10), lpad('7481', 10000), squad[0]))
				for unit in squad[1:]:
					lines.append('|   |     |%s' % unit)
				lines.append(header)

		for tupl in top_reinforcements:
			squad, count, percent = tupl
			if compact:
				lines.append(sep)
				lines.append(percent)
				lines.append(count)
				for unit in squad:
					lines.append(unit)
			else:
				lines.append('|%s|%s|%s' % (lpad(percent, 10), lpad(count, 10000), squad[0]))
				for unit in squad[1:]:
					lines.append('|   |     |%s' % unit)
				lines.append(header)

		desc = 'You can find the full meta report for top fleet arena reinforcements at this address:\n%s#reinforcements' % META_SHIPS_URL
		full_desc = '%s\n```\n| %% |Count|Ship\n%s\n%s```' % (desc, header, '\n'.join(lines))
		compact_desc = '%s\n```\n%%\nCount\nShip\n%s```' % (desc, '\n'.join(lines))

		msgs.append({
			'title': 'Top %d - Fleet Arena Reinforcements' % top_n,
			'author': {
				'name': 'Imperial Probe Droid',
				'icon_url': 'http://zeroday.biz/media/imperial-probe-droid.jpg',
			},
			'description': compact and compact_desc or full_desc,
		})


	return msgs
