#!/usr/bin/env python3

import json
import traceback
from datetime import datetime
from discord.ext import commands, tasks

from opts import *
from errors import *

import DJANGO
from swgoh.models import Player, User, UserConfig

class ChatCog(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.client = bot.client
		self.config = bot.config
		self.logger = bot.logger
		self.redis = bot.redis

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):

		if isinstance(error, commands.CommandNotFound):
			return

		raise error
		await ctx.send('\n'.join(lines))

	@commands.command(aliases=['sct'])
	async def set_chat_topic(self, ctx, *, channel_topic: str = ''):

		premium_user = parse_opts_premium_user(ctx.author)
		if not premium_user:
			return error_not_premium()

		room = await self.client.set_chat_topic(creds_id=premium_user.creds_id, player_id=premium_user.player.player_id, channel_topic=channel_topic)
		message = room and 'OK' or 'KO'
		await ctx.send(message)
