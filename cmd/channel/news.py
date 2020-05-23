from opts import *

import DJANGO
from swgoh.models import NewsChannel, NewsEntry

import inspect
from discord import ChannelType, Forbidden, HTTPException

WEBHOOK = 'SWGOH News Feed'

help_news = {
	'title': 'News Help',
	'description': """Helps you to stay up-to-date with official news from the game developers.

**Syntax**
Enabling news on a channel:
```
%prefixnews enable```
Disabling news on a channel:
```
%prefixnews disable```
Populate current channel with all passed news:
(There will be a **LOT** of entries)
```
%prefixnews history```"""
}

async def handle_news_enable(ctx):

	bot = ctx.bot
	args = ctx.args
	author = ctx.author
	channel = ctx.channel
	config = ctx.config

	if not bot.is_ipd_admin(author):
		return [{
			'title': 'Permission Denied',
			'color': 'red',
			'description': 'Only a member of the role **%s** can perform this operation.' % config['role'],
		}]

	perms = channel.permissions_for(channel.guild.me)
	if not perms.manage_webhooks:
		return [{
			'title': 'Permission Denied',
			'color': 'red',
			'description': 'I don\'t have permission to manage WebHooks in this channel. I need the following permission to proceed:\n- **Manage Webhooks**',
		}]

	webhook = None
	webhooks = await channel.webhooks()
	for awebhook in webhooks:
		if awebhook.name.lower() == WEBHOOK.lower():
			webhook = awebhook
			break
	else:
		try:
			webhook = await channel.create_webhook(name=WEBHOOK, avatar=config['bot'].get_avatar())

		except HTTPException:
			return [{
				'title': 'Webhook Creation Failed',
				'color': 'red',
				'description': 'Creation of the webhook failed due to a network error. Please try again.',
			}]

		except Forbidden:
			return [{
				'title': 'Webhook Creation Failed',
				'color': 'red',
				'description': 'I\'m not allowed to create webhooks. I need the following permission to proceed:\n- **Manage Webhooks**',
			}]

	try:
		last_news = NewsEntry.objects.all().latest('published')

	except NewsEntry.DoesNotExist:
		last_news = None

	news_channel, created = NewsChannel.objects.get_or_create(channel_id=channel.id, webhook_id=webhook.id, last_news=last_news)
	title = 'News Channel'
	desc = 'News are already enabled on this channel.'
	if created:
		title = 'News Channel'
		desc = 'News are now enabled on this channel.'

	return [{
		'title': title,
		'description': desc,
	}]

def handle_news_disable(ctx):

	bot = ctx.bot
	author = ctx.author
	channel = ctx.channel
	config = ctx.config

	if not bot.is_ipd_admin(author):
		return [{
			'title': 'Permission Denied',
			'color': 'red',
			'description': 'Only a member of the role **%s** can perform this operation.' % config['role'],
		}]

	try:
		channel = NewsChannel.objects.get(channel_id=channel.id)
		channel.delete()

	except NewsChannel.DoesNotExist:
		return bot.errors.not_a_news_channel(ctx)


	return [{
		'title': 'News Channel',
		'description': 'News are now disabled on this channel.'
	}]

async def handle_news_history(ctx):

	bot = ctx.bot
	author = ctx.author
	channel = ctx.channel
	config = ctx.config

	if not bot.is_ipd_admin(author):
		return [{
			'title': 'Permission Denied',
			'color': 'red',
			'description': 'Only a member of the role **%s** can perform this operation.' % bot.config['role'],
		}]

	try:
		channel = NewsChannel.objects.get(channel_id=channel.id)

	except NewsChannel.DoesNotExist:
		return bot.errors.not_a_news_channel(ctx)

	channel.last_news = None
	channel.save()

	await bot.update_news_channel(config, channel)

	return []

subcommands = {
	'enable':  handle_news_enable,
	'disable': handle_news_disable,
	'history': handle_news_history,
}

def parse_opts_subcommands(ctx):

	args = ctx.args
	args_cpy = list(args)
	for arg in args_cpy:
		larg = arg.lower()
		if larg in subcommands:
			args.remove(arg)
			return larg

	return None

async def cmd_news(ctx):

	bot = ctx.bot
	config = ctx.config
	command = ctx.command

	subcommand = parse_opts_subcommands(ctx)
	if not subcommand:
		return bot.errors.missing_parameter(ctx, command)

	if subcommand in subcommands:
		if inspect.iscoroutinefunction(subcommands[subcommand]):
			return await subcommands[subcommand](ctx)
		else:
			return subcommands[subcommand](ctx)

	return bot.errors.generic('Unsupported Action', subcommand)
