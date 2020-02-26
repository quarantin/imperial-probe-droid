#!/usr/bin/env python3

import sys
import json
import asyncio
import discord

my_guild = {
	'channel_id': 682302185085730910,
	'members': [
		'717952293',
		'823138241',
		'679953994',
		'285791283',
		'151522739',
		'791187582',
		'796768616',
		'963851733',
		'249146726',
		'764433286',
		'349916511',
		'313811128',
		'299618942',
		'841628554',
		'689384858',
		'432487688',
		'159773229',
		'386333955',
		'183566241',
		'939217396',
		'679624581',
		'841136222',
		'861695949',
		'788498477',
		'679283652',
		'835375258',
		'364187935',
		'919446723',
		'439553819',
		'622536847',
		'693322138',
		'721916843',
		'243118455',
		'577321579',
		'859732948',
		'423694941',
		'473387221',
		'126851788',
		'674676931',
		'275786885',
		'158895788',
		'896688629',
		'361119762',
		'349423868',
		'746734837',
	]
}

class GuildTrackerThread(asyncio.Future):

	def get_relic(self, unit):

		if 'relic' in unit and unit['relic'] and 'currentTier' in unit['relic']:
			return unit['relic']['currentTier']

		return 0

	def check_diff_player_units(self, old_profile, new_profile, messages):

		old_roster = old_profile['roster']

		old_player_name = old_profile['profile']['name']
		new_player_name = new_profile['profile']['name']
		if old_player_name != new_player_name:
			messages.append('Player **%s** has changed nickname to **%s**.' % (old_player_name, new_player_name))

		for base_id, new_unit in new_profile['roster'].items():

			# TODO Retrieve localized unit name.
			unit_name = base_id

			# Handle new units unlocked.

			if base_id not in old_roster:
				messages.append('Player **%s** unlocked **%s**.' % (new_player_name, unit_name))
				continue

			# Handle unit level increase.
			
			old_level = old_roster[base_id]['level']
			new_level = new_unit['level']
			if old_level < new_level:
				messages.append('Player **%s** promoted **%s** to level %d.' % (new_player_name, unit_name, new_level))

			# Handle unit rarity increase.

			old_rarity = old_roster[base_id]['rarity']
			new_rarity = new_unit['rarity']
			if old_rarity < new_rarity:
				messages.append('Player **%s** promoted **%s** to %d stars.' % (new_player_name, unit_name, new_rarity))

			# Handle gear level increase.

			old_gear_level = old_roster[base_id]['gear']
			new_gear_level = new_unit['gear']
			if old_gear_level < new_gear_level:
				messages.append('Player **%s** increased **%s** to gear %d.' % (new_player_name, unit_name, new_gear_level))

			# Handle relic increase.

			old_relic = self.get_relic(old_roster[base_id])
			new_relic = self.get_relic(new_unit)
			if old_relic < new_relic:
				messages.append('Player **%s** increased **%s** to relic %d.' % (new_player_name, unit_name, new_relic))

			# TODO Handle when there was a gear level change because in that case we need to do things differently
			old_equipped = old_roster[base_id]['equipped']
			new_equipped = new_unit['equipped']
			diff_equipped = [ x for x in new_equipped if x not in old_equipped ]
			if diff_equipped:
				for gear in diff_equipped:
					# TODO Retrieve localized gear name.
					gear_name = gear['equipmentId']
					messages.append('Player **%s** set **%s** on **%s**.' % (new_player_name, gear_name, unit_name))

			old_skills = { x['id']: x for x in old_roster[base_id]['skills'] }
			new_skills = { x['id']: x for x in new_unit['skills'] }

			for new_skill_id, new_skill in new_skills.items():

				# TODO Retrieve localized skill name.
				skill_name = new_skill_id

				if new_skill_id not in old_skills:
					messages.append('Player **%s** unlocked new skill **%s** for **%s**.' % (new_player_name, skill_name, unit_name))
					continue

				# TODO Check if omega or zeta and print different message in that case.
				old_skill = old_skills[new_skill_id]

				if 'tier' not in old_skill:
					old_skill['tier'] = 0

				if 'tier' not in new_skill:
					new_skill['tier'] = 0

				if old_skill['tier'] < new_skill['tier']:
					messages.append('Player **%s** increased skill **%s** for **%s** to tier %d.' % (new_player_name, skill_name, unit_name, new_skill['tier']))

		
	def check_diff_player_level(self, old_profile, new_profile, messages):

		new_player_level = new_profile['profile']['level']
		old_player_level = old_profile['profile']['level']

		if old_player_level < new_player_level:
			messages.append('Player %s reached level %d.' % (profile['profile']['name'], new_player_level))

	def check_diff(self, old_profile, new_profile, messages):

		self.check_diff_player_level(old_profile, new_profile, messages)

		self.check_diff_player_units(old_profile, new_profile, messages)

		return messages
		
	def update_player(self, ally_code, profile):

		roster = {}
		if 'roster' in profile:
			roster = { x['defId']: x for x in profile['roster'] }

		new_profile = {
			'profile': profile,
			'roster': roster,
		}

		if ally_code not in self.db:
			self.db[ally_code] = new_profile

		old_profile = self.db[ally_code]

		messages = self.check_diff(old_profile, new_profile, [])

		self.db[ally_code] = new_profile

		return messages

	async def run(self, guild_tracker):

		import DJANGO
		from swgoh.models import Shard, ShardMember
		import libswgoh
		import libprotobuf

		self.db = {}

		first_pass = True

		while True:

			session = await libswgoh.get_auth_guest()

			# TODO Retrieve guild mates in a dynamic way.
			shards = [ my_guild ]
			for shard in shards:

				messages = []
				members = shard['members']

				for member in members:

					ally_code = str(member)
					profile = await libswgoh.get_player_profile(ally_code=ally_code, session=session)

					messages = self.update_player(ally_code, profile)
					for message in messages:
						print(message)
						await guild_tracker.channel.send(message)

			if first_pass is True:
				first_pass = False
				print('Done with first pass!')

			await asyncio.sleep(60)

class GuildTracker(discord.Client):

		channel = None

		async def on_ready(self):

			self.channel = self.get_channel(my_guild['channel_id'])

			print("Guild tracker bot ready!")
			if hasattr(self, 'initialized'):
				return

			setattr(self, 'initialized', True)

			self.loop.create_task(GuildTrackerThread().run(self))

config_file = 'config.json'
fin = open(config_file, 'r')
config = json.loads(fin.read())
fin.close()

if 'tokens' not in config:
	print('Key "tokens" missing from config %s' % config_file, file=sys.stderr)
	sys.exit(-1)

if 'arena-tracker' not in config['tokens']:
	print('Key "arena-tracker" missing from config %s' % config_file, file=sys.stderr)
	sys.exit(-1)


import logging
logging.basicConfig(level=logging.INFO)

GuildTracker().run(config['tokens']['arena-tracker'])
