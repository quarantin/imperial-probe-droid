#!/usr/bin/env python3

import sys
import json
import discord
import traceback

import bot
from constants import *
from utils import translate
from swgohhelp import get_unit_name, get_ability_name

import DJANGO
from swgoh.models import Player, PremiumGuild, BaseUnitSkill

class Tracker(bot.Bot):

	def parse_opts_boolean(self, value):

		lvalue = value.lower()

		if lvalue in [ 'on', 'true', 'enable', 'enabled' ]:
			return True

		if lvalue in [ 'off', 'false', 'disable', 'disabled' ]:
			return False

		return None

	def parse_opts_channel(self, value):

		try:
			return int(value)

		except:
			pass

		import re
		match = re.search(r'^<#([0-9]+)>$', value)
		if match:
			return int(match.group(1))

		return None

	def parse_opts_mention(self, value):

		try:
			return int(value)

		except:
			pass

		import re
		match = re.search(r'^<@!?([0-9]+)>$', value)
		if match:
			return int(match.group(1))

		return None

	def get_avatar(self):
		with open('images/imperial-probe-droid.jpg', 'rb') as image:
			return bytearray(image.read())

	def get_format(self, config, param):

		key = '%s.format' % param
		if key in config:
			return config[key]

		if param in PremiumGuild.MESSAGE_FORMATS:
			return PremiumGuild.MESSAGE_FORMATS[param]

	def get_webhook_name(self):
		return 'IPD Tracker'

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

		except discord.HTTPException as err:
			errmsg = 'I was not able to create the webhook in <#%s> due to a network error: `%s`\nPlease try again.' % (channel.id, err)
			return None, errmsg

	def get_user_nick(self, server, ally_code):

		try:
			players = Player.objects.filter(ally_code=ally_code)

			for player in players:
				if player.discord_id:
					nick = '<@!%s>' % player.discord_id
					member = server and server.get_member(player.discord_id)
					avatar = member and member.avatar_url or None
					return nick, avatar

		except Player.DoesNotExist:
			pass

		self.logger.info('prepare_nick: Could not find player with allycode: %s' % ally_code)
		return None, None

	def prepare_message(self, server, config, message):

		if 'key' in message and 'nick' in message and 'ally.code' in message:
			prep_key = '%s.%s.mention' % (message['key'], message['ally.code'])
			nick, avatar = self.get_user_nick(server, message['ally.code'])
			if nick and prep_key in config and config[prep_key] is not False:
				message['mention'] = nick
			if avatar:
				message['user.avatar'] = avatar
		else:
			print('WOOHOO')
			print(json.dumps(message, indent=4))

		if 'unit' in message:
			message['unit.id'] = message['unit']
			message['unit'] = get_unit_name(message['unit'], config['language'])

		if 'gear.level' in message:
			gear_level = message['gear.level']
			message['gear.level.roman'] = ROMAN[gear_level]

		if 'gear.piece' in message:
			message['gear.piece'] = translate(message['gear.piece'], config['language'])

		if 'skill' in message:
			message['skill.id'] = message['skill']
			message['skill'] = get_ability_name(message['skill'], config['language'])

		if 'tier' in message:

			message['type'] = ''
			if int(message['tier']) >= MAX_SKILL_TIER:
				try:
					skill = BaseUnitSkill.objects.get(skill_id=message['skill.id'])
					message['type'] = skill.is_zeta and 'zeta' or 'omega'

				except BaseUnitSkill.DoesNotExist:
					self.logger.error('Could not find base unit skill with id: %s' % message['skill.id'])

		return message

	def replace_tokens(self, template, message):

		for key, value in message.items():

			token = '${%s}' % key
			if token in template:
				template = template.replace(token, str(value))

		return template

	def format_message(self, message, message_format):

		if message_format.startswith('{'):
			try:
				jsonmsg = json.loads(message_format)
				for jkey, jval in jsonmsg.items():

					if type(jval) is str:
						jsonmsg[jkey] = self.replace_tokens(jval, message)

					elif type(jval) is list:
						for item in jval:
							for skey, sval in item.items():
								if type(sval) is str:
									item[skey] = self.replace_tokens(sval, message)

					elif type(jval) is dict:
						for skey, sval in jval.items():
							if type(sval) is str:
								jval[skey] = self.replace_tokens(sval, message)

					else:
						raise Exception('This should never happen!')

				return jsonmsg

			except Exception as err:
				self.logger.error(err)
				self.logger.error(traceback.format_exc())
				return None

		for key, value in message.items():
			message_format = message_format.replace('${%s}' % key, str(value))

		return message_format

	async def on_ready(self):

		attr = 'initialized'
		if not hasattr(self, attr):

			setattr(self, attr, True)

			from trackercog import TrackerCog
			self.add_cog(TrackerCog(self))

			print('Starting tracker thread.')

			from trackerthread import TrackerThread
			self.loop.create_task(TrackerThread().run(self))

		msg = 'Tracker bot ready!'
		print(msg)
		await self.get_channel(575654803099746325).send(msg)

if __name__ == '__main__':

	from config import load_config, setup_logs

	tracker_logger = setup_logs('tracker', 'logs/tracker.log')
	discord_logger = setup_logs('discord', 'logs/tracker-discord.log')

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
		tracker.logger = tracker_logger
		tracker.redis = config.redis
		tracker.run(config['tokens']['tracker'])

	except:
		print(traceback.format_exc())
