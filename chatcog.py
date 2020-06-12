#!/usr/bin/env python3

import json
import traceback
from datetime import datetime
from discord.ext import commands, tasks

import cog

import DJANGO
from swgoh.models import Player, PlayerConfig

class ChatCog(cog.Cog):

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):

		if isinstance(error, commands.CommandNotFound):
			return

		#raise error
		#await ctx.send('\n'.join(lines))

	@commands.command(aliases=['sct'])
	async def set_chat_topic(self, ctx, *, channel_topic: str = ''):

		# TODO handle alt accounts
		ctx.alt = self.options.parse_alt([])
		premium_user = self.options.parse_premium_user(ctx)
		if not premium_user:
			return self.errors.not_premium()

		room = await self.client.set_chat_topic(creds_id=premium_user.creds_id, player_id=premium_user.player.player_id, channel_topic=channel_topic)
		message = room and 'OK' or 'KO'
		await ctx.send(message)
