#!/usr/bin/python

help_sheets = {
	'title': 'List Spreadsheets',
	'description': """Shows list of spreadsheets to share among your team.

**Syntax**
```
%prefixsheets [name]```

**Aliases**
```
%prefixS```

**Examples**
```
%prefixS
%prefixS allies```""",
}

def cmd_sheets(config, author, channel, args):

	sheets = {}
	for arg in args:

		if arg in SHEETS_ALIASES:
			arg = SHEETS_ALIASES[arg]

		if arg in config['sheets']:
			sheets[arg] = config['sheets'][arg]

	if not sheets:
		sheets = config['sheets']

	lines = []
	for name, urls in sorted(sheets.items()):
		lines.append('**`%s`**: %s' % (name, urls['edit']))

	return [{
		'title': 'Sheets',
		'description': '\n'.join(lines),
	}]