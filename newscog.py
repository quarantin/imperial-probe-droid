#!/usr/bin/env python3

import pytz
import feedparser
import traceback
from time import mktime
from datetime import datetime

from discord import Forbidden, HTTPException, InvalidData, NotFound
from discord.ext import commands, tasks

import cog
from bot import Bot

import DJANGO
from swgoh.models import NewsChannel, NewsEntry, NewsFeed

class NewsCog(cog.Cog):

	news_webhook_name = 'SWGOH News Feed'

	brief = '**`news`**: Keep track of official news from the game developers.'
	help = """Helps you to stay up-to-date with official news from the game developers.

**Syntax**
Enabling news on a channel:
```
%prefixnews enable```
Disabling news on a channel:
```
%prefixnews disable```
Populate current channel with all passed news (there will be a **LOT** of entries):
```
%prefixnews history```
"""

	def __init__(self, bot):
		super().__init__(bot)
		self.news_updater.start()

	def cog_unload(self):
		self.news_updater.cancel()

	@tasks.loop(minutes=1)
	async def news_updater(self):

		feed_urls = 'feeds' in self.config and self.config['feeds'] or {}
		for feed_name, feed_url in feed_urls.items():

			feed, created = NewsFeed.objects.get_or_create(name=feed_name, url=feed_url)
			news = feedparser.parse(feed_url)
			for entry in news.entries:
				published = datetime.fromtimestamp(mktime(entry.published_parsed), tz=pytz.UTC)
				entry, created = NewsEntry.objects.get_or_create(link=entry.link, published=published, feed=feed)

		await self.update_all_news_channels()

	@news_updater.before_loop
	async def before_news_updater(self):
		await self.bot.wait_until_ready()

	async def update_all_news_channels(self, limit=None):
		news_channels = NewsChannel.objects.all()
		for news_channel in news_channels:
			await self.update_news_channel(news_channel, limit=limit)

	async def update_news_channel(self, news_channel, limit=None):

		channel, error = await self.bot.fetch_channel_by_id(news_channel.channel_id)
		if error:
			if error in [ Bot.ERROR_NOT_FOUND, Bot.ERROR_FORBIDDEN ]:
				news_channel.delete()
			return

		webhook, error = await self.bot.fetch_webhook_by_id(news_channel.webhook_id)
		if error:
			if error in [ Bot.ERROR_NOT_FOUND, Bot.ERROR_FORBIDDEN ]:
				news_channel.delete()
			return

		last_news_date = news_channel.last_news and news_channel.last_news.published or datetime(1970, 1, 1, tzinfo=pytz.UTC)
		items = list(NewsEntry.objects.filter(published__gt=last_news_date).order_by('published'))
		if limit is not None and len(items) > limit:
			start = len(items) - limit
			items = items[start:]

		for item in items:
			content = '**%s**\n%s' % (item.feed.name, item.link)
			await webhook.send(content=content, avatar_url=webhook.avatar_url)
			news_channel.last_news = item
			news_channel.save()

	@commands.group(help=help, brief=brief)
	async def news(self, ctx):
		pass

	@news.command()
	async def enable(self, ctx):

		if not self.bot.is_ipd_admin(ctx.author):
			return await self.bot.send_embed(ctx, self.errors.admin_restricted())

		perms = ctx.channel.permissions_for(ctx.me)
		if not perms.manage_webhooks:
			return await self.bot.send_embed(ctx, self.errors.manage_webhooks_forbidden())

		webhook, error = await self.bot.get_or_create_webhook(ctx.channel, self.news_webhook_name)
		if error:
			if error == Bot.ERROR_FORBIDDEN:
				return await self.bot.send_embed(ctx, self.errors.manage_webhooks_forbidden())

			if error == Bot.ERROR_HTTP:
				return await self.bot.send_embed(ctx, self.errors.create_webhook_failed())

			return await self.bot.send_embed(ctx, self.errors_unknown_error())

		try:
			last_news = NewsEntry.objects.all().latest('published')

		except NewsEntry.DoesNotExist:
			last_news = None

		print('channel_id = %s' % ctx.channel.id)
		print('webhook_id = %s' % webhook.id)
		print('last_news  = %s' % last_news)

		news_channel, created = NewsChannel.objects.get_or_create(channel_id=ctx.channel.id, webhook_id=webhook.id, defaults={ 'last_news': last_news })

		await self.bot.send_embed(ctx, [{
			'title': 'News Channel',
			'description': created and 'News have been successfully enabled on this channel.' or 'News are already enabled on this channel.',
		}])

	@news.command()
	async def disable(self, ctx):

		if not self.bot.is_ipd_admin(ctx.author):
			return await self.bot.send_embed(ctx, self.errors.admin_restricted())

		try:
			channel = NewsChannel.objects.get(channel_id=ctx.channel.id)
			channel.delete()

		except NewsChannel.DoesNotExist:
			return await self.bot.send_embed(ctx, self.errors.not_a_news_channel(ctx))

		return await self.bot.send_embed(ctx, [{
			'title': 'News Channel',
			'description': 'News are now disabled on this channel.',
		}])

	@news.command()
	async def history(self, ctx, limit: int = 10):

		if not self.bot.is_ipd_admin(ctx.author):
			return self.bot.send_embed(self.errors.admin_restricted())

		try:
			channel = NewsChannel.objects.get(channel_id=ctx.channel.id)

		except NewsChannel.DoesNotExist:
			return self.errors.not_a_news_channel(ctx)

		channel.last_news = None
		channel.save()

		await self.update_news_channel(channel, limit)

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):

		if isinstance(error, commands.CommandNotFound):
			return

		raise error
