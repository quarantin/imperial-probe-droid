#!/usr/bin/python3

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
		'description': 'No such command \'%s\'' % command,
	}]

def error_no_ally_code_specified(config, author):
	return [{
		'title': 'Error: Not Found',
		'color': 'red',
		'description': 'No ally code specified or found registered to <@%s>. Please see `%shelp register` to get help with registration.' % (author.id, config['prefix']),
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
def error_missing_parameter(command):
	return [{
		'title': 'Error: Missing Parameter',
		'color': 'red',
		'description': 'Please see !help %s.' % command,
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
		'description': 'You have to provide a mod filter.\nPlease check %shelp wntm for more information.' % config['prefix'],
	}]

def error_permission_denied():
	return [{
		'title': 'Permission Denied',
		'color': 'red',
		'description': 'You\'re not allowed to run this command, only an admin can.',
	}]
