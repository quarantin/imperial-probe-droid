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
from swgoh.models import Player, PremiumGuild, BaseUnit, BaseUnitSkill

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

	def prepare_message(self, server, config, message):

		if 'user' in message:
			message['mention'] = message['user']

		if 'key' in message and 'user' in message and 'ally.code' in message:
			pref_key = '%s.%s.mention' % (message['key'], message['ally.code'])
			mention, avatar = self.get_user_info(server, message['ally.code'])
			if mention and pref_key in config and config[pref_key] is not False:
				message['mention'] = mention
			message['user.avatar'] = avatar

		if 'unit.id' in message:
			message['unit'] = get_unit_name(message['unit.id'], config['language'])
			message['alignment'] = BaseUnit.get_alignment(message['unit.id'])

		for key in [ 'gear', 'gear.new', 'gear.old' ]:
			if key in message:
				roman_key = 'roman.%s' % key
				message[roman_key] = ROMAN[ message[key] ]

		if 'equip.id' in message:
			message['equip'] = translate(message['equip.id'], config['language'])

		for suffix in [ '', '.new', '.old' ]:
			key = 'rarity%s' % suffix
			if key in message:
				rarity = int(message[key])
				star_key = 'stars%s' % suffix
				message[star_key] = ('★' * rarity) + ('☆' * (MAX_RARITY - rarity))

		if 'skill.id' in message:
			message['skill'] = get_ability_name(message['skill.id'], config['language'])

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

		server_token = '${server}'
		if 'server' in self.config and server_token in template:
			template = template.replace(server_token, self.config.get_server_url())

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
				print(err)
				print(traceback.format_exc())
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

		print('Tracker bot ready!')

if __name__ == '__main__':

	from config import load_config, setup_logs

	tracker_logger = setup_logs('tracker', 'logs/tracker.log')
	unreged_logger = setup_logs('tracker', 'logs/tracker-unregistered.log')
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
		tracker.logger_unreg = unreged_logger
		tracker.redis = config.redis
		tracker.run(config['tokens']['tracker'])

	except:
		print(traceback.format_exc())
