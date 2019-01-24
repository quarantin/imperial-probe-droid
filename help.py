#!/usr/bin/python3

PREFIX = '------------------------------'

HELP_HELP = {
	'title': 'Imperial Probe Droid Help - Prefix: %prefix',
	'description': """------------------------------
**Botmaster(s)**: %authors
**Source Code**: %source
------------------------------
**Help commands**
**`help`**: This help menu
------------------------------
**Internal commands**
**`alias`**: Manage command aliases.
------------------------------
**Player commands**
**`arena`**: Show arena team for the supplied ally code.
**`fleet-arena`**: Show fleet arena team for the supplied ally code.
**`mods`**: Show information about mods for the supplied ally code.
**`sheets`**: Show available spreadsheets.
**`stats`**: Show statistics about equipped mods.
------------------------------"""
}

HELP_ALIAS = {
	'title': 'Alias Help',
	'description': """Manages command aliases.

**Syntax**
```
%prefixalias
%prefixalias add [alias name] [command]
%prefixalias del [alias name or alias ID]```

**Aliases**
```
al```

**Examples**
```
%prefixalias
%prefixalias add mm mods missing
%prefixalias add myalias arena custom %speed%20%name
%prefixalias del myalias
%prefixalias del 1```"""
}

HELP_ARENA = {
	'title': 'Player info',
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
	'title': 'Player info',
	'description': 'TODO',
}

HELP_SHEETS = {
	'title': 'Player info',
	'description': 'TODO',
}

HELP_STATS = {
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
s```

Modsets parameters can be any of:
```
health (or he)
defense (or de)
potency (or po)
tenacity (or te)
critical-chance (or cc)
critical-damage (or cd)
offense (or of)
speed (or sp)```

Mod shapes parameters can be any of:
```
square (or sq)
arrow (or ar)
diamond (or di)
triangle (or tr)
circle (or ci)
cross (or cr)```

**Example**
```
%prefixs
%prefixs 123456789
%prefixs speed
%prefixs cd tr
%prefixs speed arrow
%prefixs 123456789 speed arrow```"""
}

HELP_MESSAGES = {
	'al': HELP_ALIAS,
	'alias': HELP_ALIAS,
	'a': HELP_ARENA,
	'arena': HELP_ARENA,
	'f': HELP_FLEET_ARENA,
	'fa': HELP_FLEET_ARENA,
	'fleet-arena': HELP_FLEET_ARENA,
	'h': HELP_HELP,
	'help': HELP_HELP,
	'm': HELP_MODS,
	'mods': HELP_MODS,
	's': HELP_STATS,
	'stats': HELP_STATS,
	'sh': HELP_SHEETS,
	'sheets': HELP_SHEETS,
}

