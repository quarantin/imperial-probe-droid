#!/usr/bin/python3

from cmd.alias import *
from cmd.arena import *
from cmd.gcompare import *
from cmd.fight import *
from cmd.fleet import *
from cmd.format import *
from cmd.help import *
from cmd.locked import *
from cmd.meta import *
from cmd.mods import *
from cmd.nicks import *
from cmd.needed import *
from cmd.recos import *
from cmd.restart import *
from cmd.sheets import *
from cmd.stats import *
from cmd.update import *

COMMANDS = [
	{
		'command': 'alias',
		'aliases': [ 'A', 'alias' ],
		'function': cmd_alias,
		'help': help_alias,
	},
	{
		'command': 'arena',
		'aliases': [ 'a', 'arena' ],
		'function': cmd_arena,
		'help': help_arena,
	},
	{
		'command': 'gcompare',
		'aliases': [ 'gc', 'gcompare' ],
		'function': cmd_guild_compare,
		'help': help_guild_compare,
	},
	{
		'command': 'fight',
		'aliases': [ 'c', 'fight' ],
		'function': cmd_fight,
		'help': help_fight,
	},
	{
		'command': 'fleet',
		'aliases': [ 'f', 'fa', 'fleet' ],
		'function': cmd_fleet,
		'help': help_fleet,
	},
	{
		'command': 'format',
		'aliases': [ 'F', 'format' ],
		'function': cmd_format,
		'help': help_format,
	},
	{
		'command': 'help',
		'aliases': [ 'h', 'help' ],
		'function': cmd_help,
		'help': help_help,
	},
	{
		'command': 'locked',
		'aliases': [ 'l', 'locked' ],
		'function': cmd_locked,
		'help': help_locked,
	},
	{
		'command': 'meta',
		'aliases': [ 'M', 'meta' ],
		'function': cmd_meta,
		'help': help_meta,
	},
	{
		'command': 'mods',
		'aliases': [ 'm', 'mods' ],
		'function': cmd_mods,
		'help': help_mods,
	},
	{
		'command': 'nicks',
		'aliases': [ 'N', 'nicks' ],
		'function': cmd_nicks,
		'help': help_nicks,
	},
	{
		'command': 'needed',
		'aliases': [ 'n', 'needed' ],
		'function': cmd_needed,
		'help': help_needed,
	},
	{
		'command': 'recos',
		'aliases': [ 'r', 'recos' ],
		'function': cmd_recos,
		'help': help_recos,
	},
	{
		'command': 'restart',
		'aliases': [ 'R', 'restart' ],
		'function': cmd_restart,
		'help': help_restart,
	},
	{
		'command': 'sheets',
		'aliases': [ 'S', 'sheets' ],
		'function': cmd_sheets,
		'help': help_sheets,
	},
	{
		'command': 'stats',
		'aliases': [ 's', 'stats' ],
		'function': cmd_stats,
		'help': help_stats,
	},
	{
		'command': 'update',
		'aliases': [ 'U', 'update' ],
		'function': cmd_update,
		'help': help_update,
	},
]
