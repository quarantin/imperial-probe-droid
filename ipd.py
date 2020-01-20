#!/usr/bin/env python

import asyncio
import discord
import inspect
import random
import shlex
import string
import traceback
from discord.ext import commands
from config import config, load_config, load_help

from utils import *
from embed import *
from commands import *

LOGFILE = 'messages.log'

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

def log_message(message):

	date = local_time()
	if 'timezone' in config and config['timezone']:
		date = local_time(timezone=config['timezone'])

	date = date.strftime('%Y%m%d %H:%M:%S')
	server = str(message.guild) or ''
	channel = str(message.channel) or ''
	content = message.content
	author_tokens = []
	for attr in [ 'id', 'display_name', 'nick', 'name' ]:
		if hasattr(message.author, attr):
			value = getattr(message.author, attr)
			if value and str(value) not in author_tokens:
				author_tokens.append(str(value))

	author = '/'.join(author_tokens)
	source = ' - '.join([ server, channel ])

	log = '[%s][%s][%s] %s' % (date, source, author, content)
	print(log)

	fout = open(LOGFILE, 'a+')
	fout.write('%s\n' % log)
	fout.close()

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

class ImperialProbeDroid(discord.ext.commands.Bot):


	def exit(self):

		# TODO send message on quit, like animated an
		# gif of an explosion or something like that.

		self.loop.stop()
		print('User initiated exit!')

	async def sendmsg(channel, message=None, embed=None):

		error = None
		retries = 'max-retry' in config and config['max-retry'] or 3

		while retries > 0:

			try:
				msg = await channel.send(message, embed=embed)
				return True, msg.id

			except Exception as err:
				retries -= 1
				error = err

		return False, error

	async def schedule_payouts(self, config):

		import DJANGO
		from swgoh.models import Shard, ShardMember
		from crontab import CronTab

		cron = CronTab('* * * * *')

		await self.wait_until_ready()

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
						await self.on_message_handler(config, self.user, channel, 'payout', [], from_user=False)

	async def on_ready(self):

		load_help()
		if 'env' in config and config['env'] == 'prod':

			activity = discord.Activity(name='%shelp' % config['prefix'], type=discord.ActivityType.listening)
			await self.change_presence(activity=activity)

		message = compute_hello_msg()
		if 'hello' in config:
			for chan_id in config['hello']:
				channel = self.get_channel(chan_id)
				status, error = await ImperialProbeDroid.sendmsg(channel, message=message)
				if not status:
					print('Could not print to channel %s: %s' % (channel, error))

		if 'crontab' not in config:
			config['crontab'] = True
			self.loop.create_task(self.schedule_payouts(config))

		print('Logged in as %s (ID:%s)' % (self.user.name, self.user.id))

	def remove_prefix(self, prefix_list, content):

		for prefix in prefix_list:
			content = content.replace(prefix, '')

		return content.strip()

	def get_bot_prefix(self, config, message):

		import DJANGO
		from swgoh.models import DiscordServer

		try:
			server_id = None
			if message and message.guild:
				server_id = message.guild.id

			server = DiscordServer.objects.get(server_id=server_id)
			bot_prefix = server.bot_prefix

		except DiscordServer.DoesNotExist:
			bot_prefix = config['prefix']

		return bot_prefix

	def get_prefix_list(self, config, message):

		return [
			self.get_bot_prefix(config, message),
			'<@%s>' % self.user.id,
			'<@!%s>' % self.user.id,
		]

	async def on_message(self, message):

		prefix_list = self.get_prefix_list(config, message)
		for prefix in prefix_list:
			if message.content.startswith(prefix):
				break
		else:
			return

		log_message(message)

		channel = message.channel
		content = self.remove_prefix(prefix_list, message.content)
		args = shlex.split(content)
		if not args:
			return

		command = args[0]
		if command in config['aliases']:
			replaced = message.content.replace(command, config['aliases'][command])
			content = self.remove_prefix(prefix_list, replaced)
			args = shlex.split(content)
			command = args[0]

		if command.lower() in config['ignored']:
			return

		args = args[1:]

		args = [ x for x in args if x ]

		return await self.on_message_handler(config, message.author, channel, command, args)


	async def on_message_handler(self, config, author, channel, command, args, from_user=True):

		if 'help' in args or 'h' in args:
			args = [ command ]
			command = 'help'

		try:
			for cmd in COMMANDS:
				if command in cmd['aliases']:

					if inspect.iscoroutinefunction(cmd['function']):

						if cmd['command'] == 'payout':
							msgs = await cmd['function'](config, author, channel, args, from_user=from_user)
						else:
							msgs = await cmd['function'](config, author, channel, args)
					else:
						if cmd['command'] == 'payout':
							msgs = cmd['function'](config, author, channel, args, from_user=from_user)
						else:
							msgs = cmd['function'](config, author, channel, args)

					for msg in msgs:
						embeds = new_embeds(config, msg)
						for embed in embeds:
							status, error = await ImperialProbeDroid.sendmsg(channel, message='', embed=embed)
							if not status:
								print('Could not print to channel %s: %s' % (channel, error))
					break
			else:
				embeds = new_embeds(config, {
					'title': 'Error: Unknown Command',
					'color': 'red',
					'description': 'No such command: `%s`.\nPlease type `%shelp` to get information about available commands.' % (command, config['prefix']),
				})

				for embed in embeds:
					status, error = await ImperialProbeDroid.sendmsg(channel, message='', embed=embed)
					if not status:
						print('Could not print to channel %s: %s' % (channel, error))

		except Exception as err:
			print(traceback.format_exc())

			if 'crash' in config and config['crash']:
				status, error = await ImperialProbeDroid.sendmsg(channel, message=config['crash'])
				if not status:
					print('Could not print to channel %s: %s' % (channel, error))

			embeds = new_embeds(config, {
				'title': 'Unexpected Error',
				'color': 'red',
				'description': str(err),
			})

			for embed in embeds:
				status, error = await ImperialProbeDroid.sendmsg(channel, message='', embed=embed)
				if not status:
					print('Could not print to channel %s: %s' % (channel, error))

async def __main__():
	try:
		load_config()
		config['bot'] = ImperialProbeDroid(command_prefix=config['prefix'])
		config['bot'].run(config['token'])

		await config['bot'].logout()
		print('Bot quitting!')

	except Exception as err:
		print(err)

if __name__ == '__main__':
	try:
		__main__().send(None)
	except StopIteration:
		pass
