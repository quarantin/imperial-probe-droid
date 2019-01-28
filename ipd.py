#!/usr/bin/python3

import sys
import string
import random
import discord
import subprocess

from config import load_config

from utils import *
from embed import *
from swgoh import *

from cmd.alias import *
from cmd.arena import *
from cmd.fleet import *
from cmd.format import *
from cmd.help import *
from cmd.locked import *
from cmd.mods import *
from cmd.nicks import *
from cmd.needed import *
from cmd.recos import *
from cmd.restart import *
from cmd.sheets import *
from cmd.stats import *
from cmd.update import *

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

CMDS = [
	{
		'command': 'alias',
		'aliases': [ 'A', 'alias' ],
		'function': cmd_alias,
		'help': help_alias,
	},
	{
		'command': 'arena',
		'aliases': [ 'a', 'arena' ],
		'function': cmd_arena,
		'help': help_arena,
	},
	{
		'command': 'fleet',
		'aliases': [ 'f', 'fa', 'fleet' ],
		'function': cmd_fleet,
		'help': help_fleet,
	},
	{
		'command': 'format',
		'aliases': [ 'F', 'format' ],
		'function': cmd_format,
		'help': help_format,
	},
	{
		'command': 'help',
		'aliases': [ 'h', 'help' ],
		'function': cmd_help,
		'help': help_help,
	},
	{
		'command': 'locked',
		'aliases': [ 'l', 'locked' ],
		'function': cmd_locked,
		'help': help_locked,
	},
	{
		'command': 'mods',
		'aliases': [ 'm', 'mods' ],
		'function': cmd_mods,
		'help': help_mods,
	},
	{
		'command': 'nicks',
		'aliases': [ 'N', 'nicks' ],
		'function': cmd_nicks,
		'help': help_nicks,
	},
	{
		'command': 'needed',
		'aliases': [ 'n', 'needed' ],
		'function': cmd_needed,
		'help': help_needed,
	},
	{
		'command': 'recos',
		'aliases': [ 'r', 'recos' ],
		'function': cmd_recos,
		'help': help_recos,
	},
	{
		'command': 'restart',
		'aliases': [ 'R', 'restart' ],
		'function': cmd_restart,
		'help': help_restart,
	},
	{
		'command': 'sheets',
		'aliases': [ 'S', 'sheets' ],
		'function': cmd_sheets,
		'help': help_sheets,
	},
	{
		'command': 'stats',
		'aliases': [ 's', 'stats' ],
		'function': cmd_stats,
		'help': help_stats,
	},
	{
		'command': 'update',
		'aliases': [ 'U', 'update' ],
		'function': cmd_update,
		'help': help_update,
	},
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

@bot.event
async def on_ready():
	print('Logged in as %s (ID:%s)' % (bot.user.name, bot.user.id))
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
	args = message.content.strip().split(' ')
	command = args[0][1:]
	if command in config['aliases']:
		args = message.content.replace(command, config['aliases'][command]).split(' ')
		command = args[0][1:]

	args = args[1:]

	args = [ x for x in args if x ]

	if 'help' in args or 'h' in args:
		args = [ command ]
		command = 'help'

	for cmd in CMDS:
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
