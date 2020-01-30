from cmd.channel.news import *
from cmd.channel.payout import *
from cmd.guild.compare import *
from cmd.guild.ggp import *
from cmd.guild.glist import *
from cmd.guild.ulist import *
from cmd.management.alias import *
from cmd.management.config import *
from cmd.management.help import *
from cmd.management.ignore import *
from cmd.management.invite import *
from cmd.management.language import *
from cmd.management.lookup import *
from cmd.management.nicks import *
from cmd.management.register import *
from cmd.management.restart import *
from cmd.management.timezone import *
from cmd.management.update import *
from cmd.misc.meta import *
from cmd.player.arena import *
from cmd.player.compare import *
from cmd.player.gear import *
from cmd.player.list import *
from cmd.player.locked import *
from cmd.player.modcheck import *
from cmd.player.modroll import *
from cmd.player.needed import *
from cmd.player.recos import *
from cmd.player.wntm import *
from cmd.player.zetas import *

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
		'command': 'config',
		'aliases': [ 'config' ],
		'function': cmd_config,
		'help': help_config,
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
	{
		'command': 'gear',
		'aliases': [ 'g', 'gear' ],
		'function': cmd_gear,
		'help': help_gear,
	},
	{
		'command': 'ggp',
		'aliases': [ 'ggp', 'guildgp' ],
		'function': cmd_guild_gp,
		'help': help_guild_gp,
	},
	{
		'command': 'help',
		'aliases': [ 'h', 'help' ],
		'function': cmd_help,
		'help': help_help,
	},
	{
		'command': 'ignore',
		'aliases': [ 'ignore' ],
		'function': cmd_ignore,
		'help': help_ignore,
	},
	{
		'command': 'invite',
		'aliases': [ 'invite' ],
		'function': cmd_invite,
		'help': help_invite,
	},
	{
		'command': 'language',
		'aliases': [ 'lang', 'language' ],
		'function': cmd_language,
		'help': help_language,
	},
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
	{
		'command': 'modcheck',
		'aliases': [ 'mc', 'modcheck' ],
		'function': cmd_modcheck,
		'help': help_modcheck,
	},
	{
		'command': 'modroll',
		'aliases': [ 'mr', 'modroll', 'modrolls' ],
		'function': cmd_modroll,
		'help': help_modroll,
	},
	{
		'command': 'news',
		'aliases': [ 'news' ],
		'function': cmd_news,
		'help': help_news,
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
	{
		'command': 'payout',
		'aliases': [ 'po', 'payout', 'payouts' ],
		'function': cmd_payout,
		'help': help_payout,
	},
	{
		'command': 'timezone',
		'aliases': [ 'tz', 'timezone' ],
		'function': cmd_timezone,
		'help': help_timezone,
	},
	{
		'command': 'ulist',
		'aliases': [ 'ul', 'ulist' ],
		'function': cmd_unit_list,
		'help': help_unit_list,
	},
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
	},
	{
		'command': 'zetas',
		'aliases': [ 'z', 'zeta', 'zetas' ],
		'function': cmd_zetas,
		'help': help_zetas,
	},
]
