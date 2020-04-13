#!/usr/bin/env python

import traceback
from discord.ext import commands

import DJANGO
from swgoh.models import DiscordServer

class Bot(commands.Bot):

	def exit(self):
		self.loop.stop()
		self.logger.info('User initiated exit!')

	def get_avatar(self):
		with open('images/imperial-probe-droid.jpg', 'rb') as image:
			return bytearray(image.read())

	def get_bot_prefix(self, server, channel):

		server_id = None
		if hasattr(server, 'id'):
			server_id = server.id
		elif hasattr(channel, 'id'):
			server_id = channel.id

		try:
			guild = DiscordServer.objects.get(server_id=server_id)
			bot_prefix = guild.bot_prefix

		except DiscordServer.DoesNotExist:
			bot_prefix = self.config['prefix']

		return bot_prefix

	async def sendmsg(self, channel, message=None, embed=None):

		error = None
		retries = 'max-retry' in self.config and self.config['max-retry'] or 3

		while channel is not None and retries > 0:

			try:
				msg = await channel.send(message, embed=embed)
				return True, msg.id

			except Exception as err:
				retries -= 1
				error = err

		return False, error

	async def add_reaction(self, message, emoji):

		try:
			await message.add_reaction(emoji)

		except Exception as err:
			print(err)
			print(traceback.format_exc())

	async def remove_reaction(self, message, emoji):

		try:
			await message.remove_reaction(emoji, self.user)

		except Exception as err:
			print(err)
			print(traceback.format_exc())
