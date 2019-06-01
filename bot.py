#!/usr/bin/python3

import shlex
import string
import random
import discord
import traceback
from datetime import datetime
from discord.ext import commands

from config import config, load_config

from utils import *
from embed import *
from commands import *

LOGFILE = 'messages.log'

SHEETS_ALIASES = {
	'a': 'allies',
	'r': 'recommendations',
}

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

	date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
	server = message.guild
	channel = message.channel
	content = message.content
	author_tokens = []
	if message.author.id:
		author_tokens.append(str(message.author.id))
	if message.author.display_name:
		author_tokens.append(message.author.display_name)
	if hasattr(message.author, 'nick') and message.author.nick:
		author_tokens.append(message.author.nick)
	if message.author.name:
		author_tokens.append(message.author.name)

	author = '/'.join(author_tokens)

	log = '[%s][server=%s][channel=%s][author=%s] %s' % (date, server, channel, author, content)
	print(log)

	fout = open(LOGFILE, 'a+')
	fout.write('%s\n' % log)
	fout.close()

def get_bot(config):

	if hasattr(get_bot, 'bot'):
		return get_bot.bot

	get_bot.bot = commands.Bot(command_prefix=config['prefix'])
	return get_bot.bot


load_config()

bot = get_bot(config)

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

def get_game():
	return discord.Game(name='%shelp' % config['prefix'], type=2)

@bot.event
async def on_ready():
	print('Logged in as %s (ID:%s)' % (bot.user.name, bot.user.id))
	if 'env' in config and config['env'] == 'prod':
		await bot.change_presence(activity=get_game())
	load_config(bot=bot)
	message = compute_hello_msg()
	for chan_id in config['hello']:
		channel = bot.get_channel(chan_id)
		await channel.send(message)

	print('Ready!')

@bot.event
async def on_message(message):

	if not message.content.startswith(config['prefix']):
		return

	log_message(message)

	channel = message.channel
	args = shlex.split(message.content.strip())
	command = args[0][1:]
	if command in config['aliases']:
		args = shlex.split(message.content.replace(command, config['aliases'][command]))
		command = args[0][1:]

	args = args[1:]

	args = [ x for x in args if x ]

	if 'help' in args or 'h' in args:
		args = [ command ]
		command = 'help'

	embeds = []
	attachment = None

	try:
		for cmd in COMMANDS:
			if command in cmd['aliases']:
				msgs = cmd['function'](config, message.author, channel, args)
				for msg in msgs:
					embeds = new_embeds(config, msg)
					for embed in embeds:
						await channel.send(embed=embed)
				break
		else:
			embeds = new_embeds(config, {
				'title': 'Error: Unknown command',
				'color': 'red',
				'description': 'No such command: `%s`.\nPlease type `%shelp` to get information about available commands.' % (command, config['prefix']),
			})

			for embed in embeds:
				await channel.send(embed=embed)

	except Exception as err:
		print(traceback.format_exc())

		if 'crash' in config and config['crash']:
			await channel.send(config['crash'])

		embeds = new_embeds(config, {
			'title': 'Unexpected Error',
			'color': 'red',
			'description': err,
		})

		for embed in embeds:
			await channel.send(embed=embed)
