from cmd.guild.compare import *
from cmd.guild.glist import *
from cmd.management.alias import *
#from cmd.management.format import *
from cmd.management.help import *
from cmd.management.invite import *
from cmd.management.language import *
#from cmd.management.links import *
from cmd.management.lookup import *
from cmd.management.nicks import *
from cmd.management.register import *
from cmd.management.restart import *
#from cmd.management.sheets import *
from cmd.management.update import *
from cmd.misc.meta import *
from cmd.player.arena import *
from cmd.player.compare import *
#from cmd.player.fight import *
from cmd.player.gear import *
from cmd.player.list import *
from cmd.player.locked import *
#from cmd.player.mods import *
from cmd.player.needed import *
from cmd.player.recos import *
from cmd.player.shard import *
#from cmd.player.stats import *
from cmd.player.wntm import *

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
		'command': 'pc',
		'aliases': [ 'pc' ],
		'function': cmd_player_compare,
		'help': help_player_compare,
	},
	{
		'command': 'gc',
		'aliases': [ 'gc' ],
		'function': cmd_guild_compare,
		'help': help_guild_compare,
	},
	{
		'command': 'glist',
		'aliases': [ 'gl', 'glist' ],
		'function': cmd_guild_list,
		'help': help_guild_list,
	},
	#{
	#	'command': 'fight',
	#	'aliases': [ 'f', 'fight' ],
	#	'function': cmd_fight,
	#	'help': help_fight,
	#},
	#{
	#	'command': 'format',
	#	'aliases': [ 'F', 'format' ],
	#	'function': cmd_format,
	#	'help': help_format,
	#},
	{
		'command': 'gear',
		'aliases': [ 'g', 'gear' ],
		'function': cmd_gear,
		'help': help_gear,
	},
	{
		'command': 'help',
		'aliases': [ 'h', 'help' ],
		'function': cmd_help,
		'help': help_help,
	},
	{
		'command': 'invite',
		'aliases': [ 'I', 'invite' ],
		'function': cmd_invite,
		'help': help_invite,
	},
	{
		'command': 'language',
		'aliases': [ 'lang', 'language' ],
		'function': cmd_language,
		'help': help_language,
	},
	#{
	#	'command': 'links',
	#	'aliases': [ 'L', 'links' ],
	#	'function': cmd_links,
	#	'help': help_links,
	#},
	{
		'command': 'list',
		'aliases': [ 'list' ],
		'function': cmd_list,
		'help': help_list,
	},
	{
		'command': 'locked',
		'aliases': [ 'l', 'locked' ],
		'function': cmd_locked,
		'help': help_locked,
	},
	{
		'command': 'lookup',
		'aliases': [ 'lookup' ],
		'function': cmd_lookup,
		'help': help_lookup,
	},
	{
		'command': 'me',
		'aliases': [ 'me' ],
		'function': cmd_me,
		'help': help_me,
	},
	{
		'command': 'meta',
		'aliases': [ 'm', 'meta' ],
		'function': cmd_meta,
		'help': help_meta,
	},
	#{
	#	'command': 'mods',
	#	'aliases': [ 'm', 'mods' ],
	#	'function': cmd_mods,
	#	'help': help_mods,
	#},
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
		'command': 'register',
		'aliases': [ 'me', 'reg', 'register' ],
		'function': cmd_register,
		'help': help_register,
	},
	{
		'command': 'restart',
		'aliases': [ 'R', 'restart' ],
		'function': cmd_restart,
		'help': help_restart,
	},
	#{
	#	'command': 'sheets',
	#	'aliases': [ 'S', 'sheets' ],
	#	'function': cmd_sheets,
	#	'help': help_sheets,
	#},
	{
		'command': 'shard',
		'aliases': [ 'shard' ],
		'function': cmd_shard,
		'help': help_shard,
	},
	{
		'command': 'fshard',
		'aliases': [ 'fshard' ],
		'function': cmd_fshard,
		'help': help_fshard,
	},
	#{
	#	'command': 'stats',
	#	'aliases': [ 's', 'stats' ],
	#	'function': cmd_stats,
	#	'help': help_stats,
	#},
	{
		'command': 'update',
		'aliases': [ 'U', 'update' ],
		'function': cmd_update,
		'help': help_update,
	},
	{
		'command': 'wntm',
		'aliases': [ 'w', 'wntm' ],
		'function': cmd_wntm,
		'help': help_wntm,
	}
]
