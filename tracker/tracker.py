#!/usr/bin/env python3

import sys
import traceback

import discord
from discord.ext import commands

from config import load_config, setup_logs

class Tracker(commands.Bot):

	def parse_opts_channel(self, value):

		import re
		match = re.search(r'^<#([0-9]+)>$', value)
		if match:
			return int(match.group(1))

		return None

	def get_avatar(self):
		with open('images/imperial-probe-droid.jpg', 'rb') as image:
			return bytearray(image.read())

	def get_webhook_name(self, key):
		return 'IPD Tracker %s' % key

	async def get_webhook(self, name, channel):

		try:
			webhooks = await channel.webhooks()
			for webhook in webhooks:
				if webhook.name.lower() == name.lower():
					return webhook, None

		except discord.Forbidden:
			errmsg = 'I\'m not allowed to create webhooks in <#%s>.\nI need the following permission to proceed:\n- __**Manage Webhooks**__' % channel.id
			return None, errmsg

		except discord.HTTPException:
			errmsg = 'I was not able to retrieve the webhook in <#%s> due to a network error.\nPlease try again.' % channel.id
			return None, errmsg

		return None, None

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

		except discord.HTTPException:
			errmsg = 'I was not able to create the webhook in <#%s> due to a network error.\nPlease try again.' % channel.id
			return None, errmsg

	async def on_ready(self):

		attr = 'initialized'
		if not hasattr(self, attr):

			setattr(self, attr, True)

			from trackercog import TrackerCog
			self.add_cog(TrackerCog(self, load_config()))

			print('Starting tracker thread.')

			from trackerthread import TrackerThread
			self.loop.create_task(TrackerThread().run(self))

		msg = 'Tracker bot ready!'
		print(msg)
		await self.get_channel(575654803099746325).send(msg)

if __name__ == '__main__':

	setup_logs('discord', 'logs/tracker-discord.log')

	config = load_config()

	if 'tokens' not in config:
		print('Key "tokens" missing from config', file=sys.stderr)
		sys.exit(-1)

	if 'tracker' not in config['tokens']:
		print('Key "tracker" missing from config', file=sys.stderr)
		sys.exit(-1)

	try:
		tracker = Tracker(command_prefix=config['prefix'])
		tracker.config = config
		tracker.run(config['tokens']['tracker'])

	except:
		print(traceback.format_exc())
