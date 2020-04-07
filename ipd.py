#!/usr/bin/env python

import pytz
import asyncio
import discord
import inspect
import random
import shlex
import string
import traceback
import feedparser
import threading
from time import mktime
from crontab import CronTab
from discord import Forbidden, HTTPException, InvalidData, NotFound
from discord.ext import commands

import bot
from config import load_config, load_help, setup_logs
from utils import *
from embed import *
from commands import *
from constants import EMOJI_HOURGLASS

import DJANGO
from swgoh.models import DiscordServer, NewsChannel, NewsEntry, NewsFeed, Player, Shard, ShardMember

PROBE_DIALOG = [
	'bIp',
	'bIp bIp',
	'bEp',
	'blEp',
	'BVN'
	'bOp',
	'brZ',
	'chInk',
	'schlIk',
	'stZS',
	'wOm',
]

def expand_word(word):

	for c in word:
		if c in string.ascii_uppercase:
			rand_count = random.randrange(2, 7)
			word = word.replace(c, c.lower() * rand_count, 1)

	return word

def compute_hello_msg():

	words = []
	word_count = random.randrange(3, 10)
	words_ref = list(PROBE_DIALOG)

	for i in range(0, word_count):

		rand_index = random.randrange(0, len(PROBE_DIALOG))
		rand_word = PROBE_DIALOG[rand_index]

		words.append(expand_word(rand_word))

	return (' '.join(words)).capitalize()

class MessageStub:

	guild = None
	channel = None
	content = None

	def __init__(self, guild, channel, content):
		self.guild = guild
		self.channel = channel
		self.content = content

class UserRequest:

	bot = None
	bot_prefix = None
	config = None
	author = None
	from_user = True
	server = None
	channel = None
	prefix_list = None
	message = None
	content = None
	is_ipd_message = False
	command = None
	args = None

	def __init__(self, config, message, from_user=True):
		self.bot = config['bot']
		self.logger = config['bot'].logger
		self.config = config
		self.author = hasattr(message, 'author') and message.author or self.bot.user
		self.from_user = from_user
		self.server = hasattr(message, 'guild') and message.guild or None
		self.channel = hasattr(message, 'channel') and message.channel or None
		self.bot_prefix = self.bot.get_bot_prefix(self.server, self.channel)
		self.prefix_list = self.__get_prefix_list()
		self.message = message
		self.content = hasattr(message, 'content') and message.content or str(message)
		self.is_ipd_message = self.__is_ipd_message()
		if self.is_ipd_message is True and from_user is True:
			self.__log_message(self.message)
		self.content = self.__remove_prefix(self.content)
		if self.is_ipd_message is False:
			return

		try:
			args = shlex.split(self.content)
		except:
			self.logger.error("PROBLEM WITH SHLEX: `%s`" % self.content)
			args = self.content.split(' ')

		if args:

			command = args[0]
			if command in config['aliases']:
				new_content = self.content.replace(command, config['aliases'][command])
				content = self.__remove_prefix(new_content)
				args = shlex.split(content)
				command = args[0]

			if command.lower() in config['ignored']:
				self.is_ipd_message = False

			args = args[1:]

			args = [ x for x in args if x ]

			if 'help' in args or 'h' in args:
				args = [ command ]
				command = 'help'

			self.command = command

		self.args = args

	def __log_message(self, message):

		date = local_time()
		if 'timezone' in self.config and self.config['timezone']:
			date = local_time(timezone=self.config['timezone'])

		date = date.strftime('%Y%m%d %H:%M:%S')

		author_tokens = []
		for attr in [ 'id', 'display_name', 'nick', 'name' ]:
			if hasattr(self.author, attr):
				value = getattr(self.author, attr)
				value_str = str(value)
				if value and value_str not in author_tokens:
					author_tokens.append(value_str)
		author = '/'.join(author_tokens)

		server_tokens = []
		server = hasattr(message.channel, 'guild') and str(message.channel.guild) or None
		if server:
			server_tokens.append(server)
		server_tokens.append(str(message.channel))
		source = ' - '.join(server_tokens)

		log = '[%s][%s][%s] %s' % (date, source, author, message.content)
		print(log)
		self.logger.info(log)

	def __remove_prefix(self, content):

		if content is None:
			return

		for prefix in self.prefix_list:
			content = content.replace(prefix, '')

		return content.strip()

	def __get_prefix_list(self):

		return [
			self.bot_prefix,
			'<@%s>' % self.bot.user.id,
			'<@!%s>' % self.bot.user.id,
		]

	def __is_ipd_message(self):

		for prefix in self.prefix_list:
			if self.content.startswith(prefix):
				return True

		return False

class ImperialProbeDroid(bot.Bot):

	config = None
	initialized = False

	async def update_news_channel(self, config, news_channel):

		try:
			channel = await self.fetch_channel(news_channel.channel_id)

		except NotFound:
			self.logger.error("Channel %s not found, deleting news channel" % news_channel)
			news_channel.delete()
			return

		except Forbidden:
			self.logger.error("I don't have permission to fetch channel %s" % news_channel)
			return

		except HTTPException:
			self.logger.error("HTTP error occured for channel %s, will try again later" % news_channel)
			return

		except InvalidData:
			self.logger.error("We received an unknown channel type from discord for channel %s!" % news_channel)
			return

		try:
			webhook = await self.fetch_webhook(news_channel.webhook_id)

		except NotFound:
			self.logger.error("Webhook for channel %s not found, deleting news channel" % news_channel)
			news_channel.delete()
			return

		except Forbidden:
			self.logger.error("I don't have permission to fetch webhook for channel %s" % news_channel)
			return

		except HTTPException:
			self.logger.error("HTTP error occured for channel %s, will try again later" % news_channel)
			return

		last_news_date = news_channel.last_news and news_channel.last_news.published or datetime(1970, 1, 1, tzinfo=pytz.UTC)
		items = NewsEntry.objects.filter(published__gt=last_news_date).distinct().order_by('published')

		for item in items:
			content = '**%s**\n%s' % (item.feed.name, item.link)
			await webhook.send(content=content, avatar_url=webhook.avatar_url)
			news_channel.last_news = item
			news_channel.save()

	async def update_news_channels(self, config):

		news_channels = NewsChannel.objects.all()
		for news_channel in news_channels:
			await self.update_news_channel(config, news_channel)

	async def schedule_update_news(self, config):

		cron = CronTab('*/10 * * * *')

		await self.wait_until_ready()

		self.logger.info("Scheduling news update.")

		while True:

			feed_urls = 'feeds' in config and config['feeds'] or {}
			for feed_name, feed_url in feed_urls.items():

				feed, created = NewsFeed.objects.get_or_create(name=feed_name, url=feed_url)
				news = feedparser.parse(feed.url)
				for entry in news.entries:
					published = datetime.fromtimestamp(mktime(entry.published_parsed), tz=pytz.UTC)
					entry, created = NewsEntry.objects.get_or_create(link=entry.link, published=published, feed=feed)

			await self.update_news_channels(config)

			await asyncio.sleep(cron.next(default_utc=True))

	async def schedule_payouts(self, config):

		cron = CronTab('* * * * *')

		await self.wait_until_ready()

		self.logger.info("Scheduling arena payouts.")

		while True:

			await asyncio.sleep(cron.next(default_utc=True))

			now = datetime.now()
			shards = Shard.objects.all()
			for shard in shards:
				hour_ok = now.hour % shard.hour_interval == 0
				minute_ok = now.minute > 0 and now.minute % shard.minute_interval == 0
				if hour_ok and minute_ok:
					members = list(ShardMember.objects.filter(shard=shard))
					if members:
						channel = self.get_channel(shard.channel_id)
						server = hasattr(channel, 'guild') and channel.guild or None
						bot_prefix = self.get_bot_prefix(server, channel)
						message = MessageStub(server, channel, '%spayout' % bot_prefix)
						request = UserRequest(config, message, from_user=False)
						await self.on_message_handler(request)

	async def on_ready(self):

		if self.initialized is True:
			print('Reconnection as %s (ID:%s)' % (self.user.name, self.user.id))
			return

		self.initialized = True

		config = self.config

		load_help()
		if 'env' in config and config['env'] == 'prod':

			activity = discord.Activity(name='%shelp' % config['prefix'], type=discord.ActivityType.listening)
			await self.change_presence(activity=activity)

		message = compute_hello_msg()
		if 'hello' in config:
			for chan_id in config['hello']:
				channel = self.get_channel(chan_id)
				status, error = await self.sendmsg(channel, message=message)
				if not status:
					self.logger.error('Could not print to channel %s: %s (1)' % (channel, error))

		self.loop.create_task(self.schedule_update_news(config))
		self.loop.create_task(self.schedule_payouts(config))

		print('Logged in as %s (ID:%s)' % (self.user.name, self.user.id))

	async def on_message(self, message):

		request = UserRequest(self.config, message)
		if request.is_ipd_message is False:
			return

		return await self.on_message_handler(request)

	async def on_message_handler(self, request):

		from swgohhelp import SwgohHelpException

		author = request.author
		channel = request.channel
		command = request.command
		config = request.config
		message = request.message

		if Player.is_banned(author):
			msgs = error_user_banned(config, author)
			for msg in msgs:
				await send_embed(self, channel, msg)

			return

		if channel is None:
			return

		try:
			for cmd in COMMANDS:
				if command in cmd['aliases']:

					if cmd['need_api']:
						await self.add_reaction(message, EMOJI_HOURGLASS)

					if inspect.iscoroutinefunction(cmd['function']):
						msgs = await cmd['function'](request)
					else:
						msgs = cmd['function'](request)

					if cmd['need_api']:
						await self.remove_reaction(message, EMOJI_HOURGLASS)

					for msg in msgs:
						await send_embed(self, channel, msg)

					break

			else:
				if 'reply-unknown' in config and config['reply-unknown'] is True:

					await send_embed(self, channel, {
						'title': 'Error: Unknown Command',
						'color': 'red',
						'description': 'No such command: `%s`.\nPlease type `%shelp` to get information about available commands.' % (command, config['prefix']),
					})

		except SwgohHelpException as swgohError:

			data = swgohError.data
			await send_embed(self, channel, {
				'title': swgohError.title,
				'color': 'red',
				'description': '**%s:** %s' % (data['error'], data['error_description']),
			})

		except Exception as err:
			self.logger.error("Error in on_message_handler...")
			self.logger.error(traceback.format_exc())

			if 'crash' in config and config['crash']:
				status, error = await self.sendmsg(channel, message=config['crash'])
				if not status:
					self.logger.error('Could not print to channel %s: %s (4)' % (channel, error))

			await send_embed(self, channel, {
				'title': 'Unexpected Error',
				'color': 'red',
				'description': str(err),
			})

async def __main__():

	#from ticketscog import TicketsCog

	try:

		ipd_logger     = setup_logs('ipd',     'logs/ipd.log')
		opts_logger    = setup_logs('opts',    'logs/ipd-blacklist.log')
		discord_logger = setup_logs('discord', 'logs/ipd-discord.log')

		config = load_config()

		bot = config['bot'] = ImperialProbeDroid(command_prefix=config['prefix'])
		bot.config = config
		bot.logger = ipd_logger
		bot.redis = config.redis
		#bot.add_cog(TicketsCog(bot))

		token = config['token']
		if 'env' in config:
			env = config['env']
			token = config['tokens'][env]

		try:
			bot.run(token)

		except Exception as err:
			print('Run was interrupted!')
			print(err)
			print(traceback.format_exc())

		await bot.logout()
		print('Bot quitting!')

	except Exception as err:
		print('bot initialization interrupted!')
		print(err)
		print(traceback.format_exc())

if __name__ == '__main__':
	try:
		__main__().send(None)
	except StopIteration:
		pass
