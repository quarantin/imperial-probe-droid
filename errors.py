def error_generic(title, description):
	return [{
		'title': title,
		'color': 'red',
		'description': description,
	}]

def error_no_such_command(command):
	return [{
		'title': 'Error: No Such Command',
		'color': 'red',
		'description': 'No such command `%s`' % command,
	}]

def error_no_ally_code_specified(config, author):
	return [{
		'title': 'Error: Not Found',
		'color': 'red',
		'description': 'No ally code specified or found registered to <@%s>. Please type `%shelp register` to get help with registration.' % (author.id, config['prefix']),
	}]

def error_ally_codes_not_registered(config, discord_ids):
	plural = len(discord_ids) > 1 and 's' or ''
	discord_mentions = [ '<@%s>' % x for x in discord_ids ]
	return [{
		'title': 'Error: Unknown Player%s' % plural,
		'color': 'red',
		'description': 'I don\'t know any ally code registered to the following user%s\n- %s.\n\nPlease type `%shelp register` for more information.' % (plural, '\n- '.join(discord_mentions), config['prefix']),
	}]

def error_not_enough_ally_codes_specified(ally_codes, limit):
	plural = limit > 1 and 's' or ''
	return [{
		'title': 'Error: Not Enough Ally Codes',
		'color': 'red',
		'description': 'I need at least %d ally code%s but you supplied only %d.' % (limit, plural, len(ally_codes)),
	}]

def error_too_many_ally_codes_specified(ally_codes, limit):
	plural = (limit == -1 or limit > 1) and 's' or ''
	return [{
		'title': 'Error: Too Many Ally Codes',
		'color': 'red',
		'description': 'I need maximum %d ally code%s but you supplied %d.' % (limit, plural, len(ally_codes)),
	}]

def error_no_unit_selected():
	return [{
		'title': 'Error: No Unit Selected',
		'color': 'red',
		'description': 'You have to provide at least one unit name.',
	}]

# TODO pass bot command prefix
def error_missing_parameter(config, command):
	return [{
		'title': 'Error: Missing Parameter',
		'color': 'red',
		'description': 'Please type `%shelp %s`.' % (config['prefix'], command),
	}]

def error_unknown_parameters(args):
	plural = len(args) > 1 and 's' or ''
	return [{
		'title': 'Error: Unknown Parameter%s' % plural,
		'color': 'red',
		'description': 'I don\'t know what to do with the following parameter%s:\n - %s' % (plural, '\n - '.join(args)),
	}]

def error_ally_code_not_found(ally_code):
	url = 'https://swgoh.gg/p/%s/' % ally_code
	return [{
		'title': 'Error: Not Found',
		'color': 'red',
		'description': 'Are you sure `%s` is a valid ally code and the account actually exists on swgoh.gg? Please visit this URL to check: %s' % (ally_code, url)
	}]

def error_no_mod_filter_selected(config):
	return [{
		'title': 'Error: No Filter Selected',
		'color': 'red',
		'description': 'You have to provide a mod filter.\nPlease type `%shelp wntm` for more information on mod filters.' % config['prefix'],
	}]

def error_register_mismatch(config, author, discord_ids, ally_codes):

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

def error_permission_denied():
	return [{
		'title': 'Error: Permission Denied',
		'color': 'red',
		'description': 'You\'re not allowed to run this command, only an admin can.',
	}]

def error_no_shard_found(config):
	return [{
		'title': 'No Shard Found',
		'description': 'No shard found associated to this channel. Please type `%shelp payouts` to learn how to create a shard.' % config['prefix'],
	}]

def error_not_a_news_channel(config):
	return [{
		'title': 'Not a News Channel',
		'description': 'News are disabled on this channel. Please type `%snews enable` to enable news.' % config['prefix'],
	}]
