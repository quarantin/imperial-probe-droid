
class BotErrors:

	def __init__(self, bot):
		self.bot = bot

	def generic(self, title, description):
		return [{
			'title': title,
			'color': 'red',
			'description': description,
		}]

	def unknown_error(self, title=None, message=None):
		return [{
			'title': title or 'Error: Unknown',
			'color': 'red',
			'description': message or 'An unknown error occured. Please report this to the developer.',
		}]

	def not_premium(self):
		return [{
			'title': 'Error: Not a Premium User',
			'color': 'red',
			'description': 'This command is only available to premium users.',
		}]

	def no_such_command(self, command):
		return [{
			'title': 'Error: No Such Command',
			'color': 'red',
			'description': 'No such command `%s`' % command,
		}]

	def no_ally_code_specified(self, ctx):
		return [{
			'title': 'Error: Not Found',
			'color': 'red',
			'description': 'No ally code specified or found registered to <@%s>. Please type `%shelp register` to get help with registration.' % (ctx.author.id, self.bot.get_bot_prefix(ctx)),
		}]

	def no_ally_code_specified_ban(self, ctx):
		return [{
			'title': 'Error: Not Found',
			'color': 'red',
			'description': 'No player selected. Please type `%shelp ban` to get help.' % self.bot.get_bot_prefix(ctx),
		}]

	def invalid_ally_codes(self, ally_codes):
		ally_codes = [ str(x) for x in ally_codes ]
		plural = len(ally_codes) > 1 and 's' or ''
		be = len(ally_codes) > 1 and 'are' or 'is'
		return [{
			'title': 'Error: Invalid Ally Code%s' % plural,
			'color': 'red',
			'description': 'The following ally code%s %s invalid:\n%s' % (plural, be, '\n'.join(ally_codes)),
		}]

	def ally_codes_not_registered(self, ctx, discord_ids):
		plural = len(discord_ids) > 1 and 's' or ''
		discord_mentions = [ '<@%s>' % x for x in discord_ids ]
		return [{
			'title': 'Error: Unknown Player%s' % plural,
			'color': 'red',
			'description': 'I don\'t know any ally code registered to the following user%s\n- %s.\n\nPlease type `%shelp register` for more information.' % (plural, '\n- '.join(discord_mentions), self.bot.get_bot_prefix(ctx)),
		}]

	def not_enough_ally_codes_specified(self, ally_codes, limit):
		plural = limit > 1 and 's' or ''
		return [{
			'title': 'Error: Not Enough Ally Codes',
			'color': 'red',
			'description': 'I need at least %d ally code%s but you supplied only %d.' % (limit, plural, len(ally_codes)),
		}]

	def too_many_ally_codes_specified(self, ally_codes, limit):
		plural = (limit == -1 or limit > 1) and 's' or ''
		return [{
			'title': 'Error: Too Many Ally Codes',
			'color': 'red',
			'description': 'I need maximum %d ally code%s but you supplied %d.' % (limit, plural, len(ally_codes)),
		}]

	def no_unit_selected(self, ctx):
		return [{
			'title': 'Error: No Unit Selected',
			'color': 'red',
			'description': 'You have to provide at least one unit name.',
			# TODO: Please type `!help units` to get help about selecting units.
		}]

	def missing_parameter(self, ctx, command):
		return [{
			'title': 'Error: Missing Parameter',
			'color': 'red',
			'description': 'Please type `%shelp %s`.' % (self.bot.get_bot_prefix(ctx), command),
		}]

	def unknown_parameters(self, args):
		plural = len(args) > 1 and 's' or ''
		return [{
			'title': 'Error: Unknown Parameter%s' % plural,
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
		}]

	def ally_code_not_found(self, ally_code):
		return [{
			'title': 'Error: Ally Code Not Found',
			'color': 'red',
			'description': 'It seems **%s** is __**NOT**__ a valid ally code.' % ally_code,
		}]

	def ally_codes_not_found(self, ally_codes):
		return [ self.ally_code_not_found(ally_code)[0] for ally_code in ally_codes ]

	def no_mod_filter_selected(self, ctx):
		return [{
			'title': 'Error: No Filter Selected',
			'color': 'red',
			'description': 'You have to provide a mod filter.\nPlease type `%shelp wntm` for more information on mod filters.' % self.bot.get_bot_prefix(ctx),
		}]

	def register_mismatch(self, ctx, discord_ids, ally_codes):

		ally_codes_str = ''
		discord_ids_str = ''

		if len(discord_ids):
			discord_ids_str = 'Here is the list of discord users:\n- %s' % '\n- '.join(discord_ids)
			if len(ally_codes):
				ally_codes_str = 'And the list of ally codes:\n- %s' % '\n- '.join(ally_codes)

		elif len(ally_codes):
			if len(ally_codes):
				ally_codes_str = 'Here is the list of ally codes:\n- %s' % '\n- '.join(ally_codes)

		return [{
			'title': 'Error: Registration Failed',
			'color': 'red',
			'description': 'You have to supply the same number of discord users and ally codes but you supplied %d discord users and %d ally codes. %s%s' % (len(discord_ids), len(ally_codes), discord_ids_str, ally_codes_str),
		}]

	def permission_denied(self):
		return [{
			'title': 'Error: Permission Denied',
			'color': 'red',
			'description': 'You\'re not allowed to run this command, only an admin can.',
		}]

	def admin_restricted(self):
		return [{
			'title': 'Permission Denied',
			'color': 'red',
			'description': 'Only a member of the role **%s** can perform this operation.' % self.bot.config['role'],
		}]

	def manage_webhooks_forbidden(self):
		return [{
			'title': 'Bot Missing Permission',
			'color': 'red',
			'description': 'I don\'t have permission to manage WebHooks in this channel. I need the following permission to proceed:\n- **Manage Webhooks**',
		}]

	def create_webhook_failed(self):
		return [{
			'title': 'WebHook Creation Failed',
			'color': 'red',
			'description': 'Creation of the webhook failed due to a network error. Please try again.',
		}]

	def no_shard_found(self, ctx):
		return [{
			'title': 'No Shard Found',
			'description': 'No shard found associated to this channel. Please type `%shelp payouts` to learn how to create a shard.' % self.bot.get_bot_prefix(ctx),
		}]

	def not_a_news_channel(self, ctx):
		return [{
			'title': 'Not a News Channel',
			'description': 'News are disabled on this channel. Please type `%snews enable` to enable news.' % self.bot.get_bot_prefix(ctx),
		}]

	def user_banned(self, ctx):
		extra = 'If you think this is a mistake, please visit my discord server and ask for help: %s\n' % self.bot.config['discord']
		return [{
			'title': 'Banned',
			'color': 'red',
			'description': 'Hi <@%s>,\n\nSorry but it appears you\'ve been banned from using my services.\n%s' % (ctx.author.id, extra),
		}]

	def invalid_guild_channel(self, ctx):
		return [{
			'title': 'Not a Guild Channel',
			'color': 'red',
			'description': 'This command can only be invoked in a text channel on your guild server.',
		}]

	def invalid_config_key(self, subcommand, ctx, config_key):
		return 'The following setting is invalid: `"%s"`.\nPlease type `%stracker %s` to get the list of valid settings.' % (config_key, self.bot.get_bot_prefix(ctx), subcommand)

	def invalid_config_value(self, subcommand, ctx, config_value):
		return 'The following value is invalid: `"%s"`.\nPlease type `%stracker %s` to get help.' % (config_value, self.bot.get_bot_prefix(ctx), subcommand)
