help_sheets = {
	'title': 'Spreadsheets Help',
	'description': """Shows list of spreadsheets to share among your team.

**Syntax**
```
%prefixsheets [name]```
**Aliases**
```
%prefixS```
**Examples**
List available spreadsheets:
```
%prefixS```
Show allies spreadsheet:
```
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
		edit_url = urls['edit']
		if edit_url in config['short-urls']:
			edit_url = config['short-urls'][edit_url]

		lines.append('**`%s`**: %s' % (name, edit_url))

	return [{
		'title': 'Sheets',
		'description': '\n'.join(lines),
	}]
