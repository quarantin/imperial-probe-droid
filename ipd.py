#!/usr/bin/python3

import shlex
import string
import random
import discord

from config import load_config

from utils import *
from embed import *
from swgoh import *
from commands import *

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

bot = discord.Client()

def expand_word(word):

	for c in string.ascii_uppercase:
		if c in word:
			rand_count = random.randrange(2, 7)
			word = word.replace(c, c.lower() * rand_count)

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
	await bot.change_presence(game=get_game())
	load_config(bot)
	message = compute_hello_msg()
	for chan_id in config['hello']:
		channel = bot.get_channel(chan_id)
		await bot.send_message(channel, message)

@bot.event
async def on_message(message):

	if not message.content.startswith(config['prefix']):
		return

	channel = message.channel
	nick = message.author.display_name or message.author.nick or message.author.name
	author = '@%s' % nick
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

	for cmd in COMMANDS:
		if command in cmd['aliases']:
			msgs = cmd['function'](config, author, channel, args)
			for msg in msgs:
				embed = new_embed(config, msg)
				await bot.send_message(channel, embed=embed)
			break
	else:
		embed = new_embed(config, {
			'title': 'Unknown command',
			'color': 'red',
			'description': 'No such command: %s' % command,
		})
		await bot.send_message(channel, embed=embed)

config = load_config()

bot.run(config['token'])

bot.close()
