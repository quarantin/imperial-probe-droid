from errors import *
from utils import check_permission

help_clear = {
	'title': 'Clear Help',
	'description': """Delete messages from current channel.\n**Be careful as this operation is irreversible.**
	
**Syntax**
```
%prefixclear [limit]```
By default limit is 10.
**Examples**
To clear the last ten messages:
```
%prefixclear```
To clear the last hundred messages:
```
%prefixclear 100```"""
}

def parse_opts_limit(args):

	args_cpy = list(args)
	for arg in args_cpy:

		try:
			limit = int(arg)
			args.remove(arg)
			return limit

		except:
			pass

	return 10

async def cmd_clear(request):

	args = request.args
	author = request.author
	bot = request.bot
	channel = request.channel
	config = request.config

	perms = channel.permissions_for(channel.guild.me)
	if not perms.manage_messages:
		return [{
			'title': 'Permission Denied',
			'color': 'red',
			'description': 'I don\'t have permission to manage messages in this channel. I need the following permission to proceed:\n- **Manage Messages**',
		}]

	if not perms.read_message_history:
		return [{
			'title': 'Permission Denied',
			'color': 'red',
			'description': 'I don\'t have permission to read message history in this channel. I need the following permission to proceed:\n- **Read Message History**',
		}]

	perms = channel.permissions_for(author)
	if not perms.manage_messages:

		if not check_permission(request):
			return [{
				'title': 'Permission Denied',
				'color': 'red',
				'description': 'Only a member of the role **%s** can perform this operation.' % config['role'],
			}]

	limit = parse_opts_limit(args)

	if args:
		return error_unknown_parameters(args)

	messages = []
	async for message in channel.history(limit=limit):
		# TODO only delete messages from IPD?
		messages.append(message)

	await channel.delete_messages(messages)

	return []
