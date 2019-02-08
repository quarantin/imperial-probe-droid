#!/usr/bin/python3

help_help = {
	'title': 'Imperial Probe Droid Help - Prefix: %prefix',
	'description': """**Botmaster(s)**: %authors
**Source Code**: %source
%separator
**Help Commands**
**`help`**: This help menu
%separator
**Internal Commands**
**`alias`**: Manage command aliases.
**`format`**: Manage output formats.
**`nicks`**: Manage nicknames for units and ships.
**`sheets`**: Show available spreadsheets.
%separator
**Guild Commands**
**`gc`**: Compare one (or more) guilds.
%separator
**Player Commands**
**`arena`**: Show arena team for the supplied ally code.
**`fleet`**: Show fleet arena team for the supplied ally code.
**`locked`**: Show locked units or ships for the supplied ally code.
**`meta`**: Show information about best arena and fleet squads.
**`mods`**: Show information about mods for the supplied ally code.
**`needed`**: Show information about needed modsets globally.
**`recos`**: Show information about recommended mods.
**`stats`**: Show statistics about equipped mods."""
}

def substitute_tokens(config, text):

	tokens = [
		'authors',
		'prefix',
		'separator',
		'source',
	]

	for token in tokens:

		value = config[token]
		if token == 'source':
			if value in config['short-urls']:
				value = config['short-urls'][value]

		if type(value) is list:
			value = ', '.join(value)

		text = text.replace('%' + token, value)

	return text

def cmd_help(config, author, channel, args):

	msg = help_help

	if args:
		command = args[0]
		if command in config['help']:
			msg = config['help'][command]

	return [{
		'title':       substitute_tokens(config, msg['title']),
		'description': substitute_tokens(config, msg['description']),
	}]
