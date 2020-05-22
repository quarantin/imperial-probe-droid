#!/usr/bin/env python

import aiohttp
import traceback
import discord
from discord.ext import commands

import DJANGO
from swgoh.models import DiscordServer, Player

class Bot(commands.Bot):

	max_retries = 3

	def exit(self):
		self.loop.stop()
		self.logger.info('User initiated exit!')

	def get_avatar(self):
		with open('images/imperial-probe-droid.jpg', 'rb') as image:
			return bytearray(image.read())

	def get_bot_prefix(self, ctx=None):

		bot_prefix = '!'

		if ctx:
			if hasattr(ctx, 'channel'):
				channel = ctx.channel
				server_id = channel.id
				if hasattr(channel, 'guild'):
					server_id = channel.guild.id

				try:
					guild = DiscordServer.objects.get(server_id=server_id)
					bot_prefix = guild.bot_prefix

				except DiscordServer.DoesNotExist:
					bot_prefix = self.config['prefix']

		return bot_prefix

	def get_perms(self):

		perms = discord.Permissions()

		perms.manage_webhooks = True
		perms.manage_messages = True
		perms.read_messages = True
		perms.read_message_history = True
		perms.send_messages = True
		perms.embed_links = True
		perms.attach_files = True
		perms.external_emojis = True
		perms.add_reactions = True

		return perms.value

	def get_invite_url(self, user=None):

		from urllib.parse import urlencode

		client_id = user is None and self.user.id or user.id

		return 'https://discordapp.com/api/oauth2/authorize?' + urlencode({
			'client_id': client_id,
			'perms': self.get_perms(),
			'scope': 'bot',
		})

	def get_invite_link(self, user=None, invite_msg='Click here to invite this bot to your server'):
		return '[%s](%s)' % (invite_msg, self.get_invite_url(user=user))

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

	async def get_webhook(self, name, channel):

		error_message = None

		max_retries = self.max_retries
		while max_retries > 0:

			try:
				webhooks = await channel.webhooks()
				for webhook in webhooks:
					if webhook.name.lower() == name.lower():
						return webhook, None

			except discord.Forbidden:
				error_message = 'I\'m not allowed to view webhooks in <#%s>.\nI need the following permission to proceed:\n- __**Manage Webhooks**__' % channel.id
				# No need to try again for permission errors
				break

			except discord.HTTPException:
				error_message = 'I was not able to retrieve the webhook in <#%s> due to a network error.\nPlease try again.' % channel.id
				# Here we want to try again so no break
				# break

			except aiohttp.ClientOSError:
				error_message = 'I was not able to retrieve the webhook in <#%s> due to a network error (2).\nPlease try again.' % channel.id
				# Here we want to try again so no break
				# break

			max_retries -= 1

		return None, error_message

	async def create_webhook(self, name, avatar, channel):

		perms = channel.permissions_for(channel.guild.me)
		if not perms.manage_webhooks:
			return [{
				'title': 'Permission Denied',
				'color': 'red',
				'description': 'I don\'t have permission to manage WebHooks in <#%s>.\nI need the following permission to proceed:\n- __**Manage Webhooks**__' % channel.id,
			}]

		try:
			webhook = await channel.create_webhook(name=name, avatar=avatar)
			return webhook, None

		except discord.Forbidden:
			errmsg = 'I\'m not allowed to create webhooks in <#%s>.\nI need the following permission to proceed:\n- __**Manage Webhooks**__' % channel.id,
			return None, errmsg

		except discord.HTTPException as err:
			errmsg = 'I was not able to create the webhook in <#%s> due to a network error: `%s`\nPlease try again.' % (channel.id, err)
			return None, errmsg

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

	def get_user_info(self, server, ally_code):

		try:
			players = Player.objects.filter(ally_code=ally_code)

			for player in players:
				if player.discord_id:
					nick = '<@!%s>' % player.discord_id
					member = server and server.get_member(player.discord_id)
					avatar = member and member.avatar_url_as(format='png', size=64) or self.user.default_avatar_url
					return nick, str(avatar)

		except Player.DoesNotExist:
			print(traceback.format_exc())

		self.logger_unreg.info('Unregistered allycode: %s (%s)' % (ally_code, server.name))
		return None, str(self.user.default_avatar_url)

	def is_ipd_admin(self, author):

		if 'role' in self.config:
			ipd_role = self.config['role'].lower()
			for role in author.roles:
				if role.name.lower() == ipd_role:
					return True

		if 'admins' in self.config:
			if author.id in self.config['admins']:
				return True

		return False
