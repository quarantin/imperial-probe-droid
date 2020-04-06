from cmd.channel.news import *
from cmd.channel.payout import *
from cmd.guild.compare import *
from cmd.guild.ggp import *
from cmd.guild.glist import *
from cmd.guild.stat import *
from cmd.guild.ulist import *
from cmd.general.alias import *
from cmd.general.ban import *
from cmd.general.clear import *
from cmd.general.clock import *
from cmd.general.config import *
from cmd.general.help import *
from cmd.general.ignore import *
from cmd.general.invite import *
from cmd.general.language import *
from cmd.general.lookup import *
from cmd.general.nicks import *
from cmd.general.register import *
from cmd.general.restart import *
from cmd.general.servers import *
from cmd.general.timezone import *
from cmd.general.update import *
from cmd.general.gregister import *
from cmd.misc.meta import *
from cmd.player.arena import *
from cmd.player.compare import *
from cmd.player.gac import *
from cmd.player.gear import *
from cmd.player.gear13 import *
from cmd.player.list import *
from cmd.player.locked import *
from cmd.player.modcheck import *
from cmd.player.modroll import *
from cmd.player.needed import *
from cmd.player.recos import *
from cmd.player.relic import *
from cmd.player.stat import *
from cmd.player.wntm import *
from cmd.player.zetas import *

COMMANDS = [
	{
		'command': 'alias',
		'aliases': [ 'A', 'alias' ],
		'function': cmd_alias,
		'help': help_alias,
		'need_api': False,
	},
	{
		'command': 'arena',
		'aliases': [ 'a', 'arena' ],
		'function': cmd_arena,
		'help': help_arena,
		'need_api': True,
	},
	{
		'command': 'ban',
		'aliases': [ 'ban' ],
		'function': cmd_ban,
		'help': help_ban,
		'need_api': False,
	},
	{
		'command': 'unban',
		'aliases': [ 'unban' ],
		'function': cmd_unban,
		'help': help_unban,
		'need_api': False,
	},
	{
		'command': 'clear',
		'aliases': [ 'clear' ],
		'function': cmd_clear,
		'help': help_clear,
		'need_api': False,
	},
	{
		'command': 'clock',
		'aliases': [ 'clock' ],
		'function': cmd_clock,
		'help': help_clock,
		'need_api': False,
	},
	{
		'command': 'config',
		'aliases': [ 'config' ],
		'function': cmd_config,
		'help': help_config,
		'need_api': False,
	},
	{
		'command': 'pc',
		'aliases': [ 'pc', 'pcompare', 'playercompare' ],
		'function': cmd_player_compare,
		'help': help_player_compare,
		'need_api': True,
	},
	{
		'command': 'ps',
		'aliases': [ 'ps', 'pstat', 'pstats', 'playerstat', 'playerstats' ],
		'function': cmd_player_stat,
		'help': help_player_stat,
		'need_api': True,
	},
	{
		'command': 'gc',
		'aliases': [ 'gc', 'gcompare', 'guildcompare' ],
		'function': cmd_guild_compare,
		'help': help_guild_compare,
		'need_api': True,
	},
	{
		'command': 'gs',
		'aliases': [ 'gs', 'gstat', 'gstats', 'guildstat', 'guildstats' ],
		'function': cmd_guild_stat,
		'help': help_guild_stat,
		'need_api': True,
	},
	{
		'command': 'glist',
		'aliases': [ 'gl', 'glist' ],
		'function': cmd_guild_list,
		'help': help_guild_list,
		'need_api': True,
	},
	{
		'command': 'gac',
		'aliases': [ 'gac' ],
		'function': cmd_gac,
		'help': help_gac,
		'need_api': True,
	},
	{
		'command': 'gear',
		'aliases': [ 'g', 'gear' ],
		'function': cmd_gear,
		'help': help_gear,
		'need_api': True,
	},
	{
		'command': 'gear13',
		'aliases': [ 'g13', 'gear13' ],
		'function': cmd_gear13,
		'help': help_gear13,
		'need_api': True,
	},

	{
		'command': 'ggp',
		'aliases': [ 'ggp', 'guildgp' ],
		'function': cmd_guild_gp,
		'help': help_guild_gp,
		'need_api': True,
	},
	{
		'command': 'help',
		'aliases': [ 'h', 'help' ],
		'function': cmd_help,
		'help': help_help,
		'need_api': False,
	},
	{
		'command': 'ignore',
		'aliases': [ 'ignore' ],
		'function': cmd_ignore,
		'help': help_ignore,
		'need_api': False,
	},
	{
		'command': 'invite',
		'aliases': [ 'invite' ],
		'function': cmd_invite,
		'help': help_invite,
		'need_api': False,
	},
	{
		'command': 'language',
		'aliases': [ 'lang', 'language' ],
		'function': cmd_language,
		'help': help_language,
		'need_api': False,
	},
	{
		'command': 'list',
		'aliases': [ 'list' ],
		'function': cmd_list,
		'help': help_list,
		'need_api': False,
	},
	{
		'command': 'locked',
		'aliases': [ 'l', 'locked' ],
		'function': cmd_locked,
		'help': help_locked,
		'need_api': True,
	},
	{
		'command': 'lookup',
		'aliases': [ 'lookup' ],
		'function': cmd_lookup,
		'help': help_lookup,
		'need_api': False,
	},
	{
		'command': 'me',
		'aliases': [ 'me' ],
		'function': cmd_me,
		'help': help_me,
		'need_api': False,
	},
	{
		'command': 'meta',
		'aliases': [ 'm', 'meta' ],
		'function': cmd_meta,
		'help': help_meta,
		'need_api': False,
	},
	{
		'command': 'modcheck',
		'aliases': [ 'mc', 'modcheck' ],
		'function': cmd_modcheck,
		'help': help_modcheck,
		'need_api': True,
	},
	{
		'command': 'modroll',
		'aliases': [ 'mr', 'modroll', 'modrolls' ],
		'function': cmd_modroll,
		'help': help_modroll,
		'need_api': True,
	},
	{
		'command': 'news',
		'aliases': [ 'news' ],
		'function': cmd_news,
		'help': help_news,
		'need_api': False,
	},
	{
		'command': 'nicks',
		'aliases': [ 'N', 'nicks' ],
		'function': cmd_nicks,
		'help': help_nicks,
		'need_api': False,
	},
	{
		'command': 'needed',
		'aliases': [ 'n', 'needed' ],
		'function': cmd_needed,
		'help': help_needed,
		'need_api': False,
	},
	{
		'command': 'recos',
		'aliases': [ 'r', 'recos' ],
		'function': cmd_recos,
		'help': help_recos,
		'need_api': True,
	},
	{
		'command': 'register',
		'aliases': [ 'me', 'reg', 'register' ],
		'function': cmd_register,
		'help': help_register,
		'need_api': True,
	},
	{
		'command': 'restart',
		'aliases': [ 'R', 'restart' ],
		'function': cmd_restart,
		'help': help_restart,
		'need_api': False,
	},
	{
		'command': 'payout',
		'aliases': [ 'po', 'payout', 'payouts' ],
		'function': cmd_payout,
		'help': help_payout,
		'need_api': True,
	},
	{
		'command': 'relic',
		'aliases': [ 'rr', 'relic', 'relics' ],
		'function': cmd_relic,
		'help': help_relic,
		'need_api': True,
	},
	{
		'command': 'servers',
		'aliases': [ 'servers' ],
		'function': cmd_servers,
		'help': help_servers,
		'need_api': False,
	},
	{
		'command': 'timezone',
		'aliases': [ 'tz', 'timezone' ],
		'function': cmd_timezone,
		'help': help_timezone,
		'need_api': False,
	},
	{
		'command': 'ulist',
		'aliases': [ 'ul', 'ulist' ],
		'function': cmd_unit_list,
		'help': help_unit_list,
		'need_api': True,
	},
	{
		'command': 'update',
		'aliases': [ 'U', 'update' ],
		'function': cmd_update,
		'help': help_update,
		'need_api': False,
	},
	{
		'command': 'gregister',
		'aliases': [ 'gr', 'greg', 'gregister', 'gregistered' ],
		'function': cmd_gregister,
		'help': help_gregister,
		'need_api': True,
	},
	{
		'command': 'wntm',
		'aliases': [ 'w', 'wntm' ],
		'function': cmd_wntm,
		'help': help_wntm,
		'need_api': False,
	},
	{
		'command': 'zetas',
		'aliases': [ 'z', 'zeta', 'zetas' ],
		'function': cmd_zetas,
		'help': help_zetas,
		'need_api': True,
	},
]
