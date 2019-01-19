#!/usr/bin/python3

HELP_HELP = {
	'title': 'Imperial Probe Droid Help - Prefix: %prefix',
	'color': 'blue',
	'description': """------------------------------
**Botmaster(s)**: %authors
**Source Code**: %source
------------------------------
**Help commands**
**`help`**: This help menu
------------------------------
**Player commands**
**`arena`**: Show arena team for the supplied ally code.
**`fleet-arena`**: Show fleet arena team for the supplied ally code.
**`mods`**: Show stats about mods for the supplied ally code.
**`sheets`**: Show spreadsheets.
"""
}

HELP_ARENA = {
	'title': 'Player info',
	'color': 'blue',
	'description': """Shows arena team for the supplied ally codes.

**Syntax**
```
%prefixarena [ally codes] [l|s|v]
%prefixarena [ally codes] c <format>```

**Options**
lite (l): lite display
short (s): short display
verbose (v): verbose display
custom (c): custom display

**Aliases**
```
a```

**Format**
The custom format can contain the following keywords:
```
%name (character name)
%leader (leader of the group)
%level (level of the character)
%gear (level of gear of the character)
%power (power of the character)
%health (health of the character)
%speed (speed of the character)
...```
Also spaces need to be replaced with %20 and newlines with %0A.

**Example**
```
%prefixa
%prefixa l
%prefixa 123456789
%prefixa 123456789 234567891
%prefixa 123456789 lite
%prefixa c %speed%20%name```"""
}

HELP_FLEET_ARENA = {
	'title': 'Player info',
	'color': 'blue',
	'description': """Shows fleet arena team for the supplied ally codes.

**Options**
lite (l)
short (s)
verbose (v)
custom (c)

**Aliases**
```
f
fa```

**Example**
```
%prefixf
%prefixf 123456789
%prefixf 123456789 234567891
%prefixf 123456788 verbose
%prefixf c %speed%20%name```"""

}

HELP_MODS = {

}

HELP_SHEETS = {

}

HELP_MESSAGES = {
	'a': HELP_ARENA,
	'arena': HELP_ARENA,
	'f': HELP_FLEET_ARENA,
	'fa': HELP_FLEET_ARENA,
	'fleet-arena': HELP_FLEET_ARENA,
	'h': HELP_HELP,
	'help': HELP_HELP,
	'm': HELP_MODS,
	'mods': HELP_MODS,
	'sh': HELP_SHEETS,
	'sheets': HELP_SHEETS,
}

