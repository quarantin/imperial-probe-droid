from errors import *
from utils import get_invite_link

help_help = {
	'title': 'Imperial Probe Droid Help - Prefix: %prefix',
	'description': """**Botmaster(s)**: %authors
**Source Code**: %source
**Need support?**: Join us on [Discord](%discord)!
**Like this bot?**: Support us on [Patreon](%patreon)!
**Invite this bot?**: Click %invite!
%separator
**General Commands**
**`help`**: This help menu.
**`help <command>`**: Get help menu for command.
**`config`**: Configure server settings such as bot prefix (**NEW**).
**`register`**: Register your ally code.
**`gregister`**: Register your guild mates (**NEW**).
**`invite`**: Invite this bot to your server.
%separator
**Channel Commands**
**`news`**: Keep track of official news from the game developers (**NEW**).
**`payout`**: Keep track of time left to payout for your shard members in arena.
%separator
**Guild Commands**
**`gc`**: Guild comparison by roster.
**`gs`**: Guild comparison by stats.
**`glist`**: List guild members by unit GP, gear, level, rarity.
%separator
**Player Commands**
**`arena`**: Show arena squad details.
**`gac`**: Compare GAC statistics of different players (**NEW**).
**`gear`**: List equipment needed for characters.
**`gear13`**: List most popular gear 13 characters you don't have (**NEW**).
**`locked`**: Show locked characters or ships.
**`mc`**: Show characters with missing mods or having weak mods (**NEW**).
**`meta`**: Show information about best arena and fleet squads.
**`needed`**: Show information about needed modsets globally.
**`pc`**: Player comparison by roster.
**`ps`**: Player comparison by stats.
**`recos`**: Show information about recommended mods.
**`relics`**: List most popular characters with relics (**NEW**).
**`wntm`**: List characters who needs mods with specific criteria.
**`zetas`**: List most popular zetas you don't have (**NEW**)."""
#NOT WORKING **`mods`**: Show information about mods.
#NOT WORKING **`stats`**: Show statistics about equipped mods."""
}

def substitute_tokens(config, text):

	tokens = [
		'authors',
		'discord',
		'invite',
		'patreon',
		'prefix',
		'separator',
		'source',
	]

	for token in tokens:

		value = token in config and config[token] or ''
		if token == 'source':
			value = '[Github](%s)' % value

		elif token == 'invite':
			value = get_invite_link(config, invite_msg='HERE')

		if type(value) is list:
			value = ', '.join(value)

		text = text.replace('%' + token, value)

	return text

def cmd_help(request):

	args = request.args
	config = request.config

	msg = help_help

	if args:
		command = args[0].lower()
		if command in config['help']:
			msg = config['help'][command]
		else:
			return error_no_such_command(command)

	return [{
		'title':       substitute_tokens(config, msg['title']),
		'description': substitute_tokens(config, msg['description']),
	}]