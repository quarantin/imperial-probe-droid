#!/usr/bin/env python3

from datetime import datetime, timedelta

import DJANGO
from swgoh.models import PremiumGuild

class CrawlerDiffer:

	def __init__(self, bot):
		self.bot = bot
		self.config = bot.config
		self.logger = bot.logger
		self.redis = bot.redis

	def get_relic(self, unit):

		if 'relic' in unit and unit['relic'] and 'currentTier' in unit['relic']:
			return max(0, unit['relic']['currentTier'] - 2)

		return 0

	def check_diff_player_units(self, guild, old_profile, new_profile, messages):

		old_roster = { x['defId']: x for x in old_profile['roster'] }
		new_roster = { x['defId']: x for x in new_profile['roster'] }

		old_player_name = old_profile['name']
		new_player_name = new_profile['name']
		if old_player_name != new_player_name:
			messages.append({
				'key': PremiumGuild.MSG_PLAYER_NICK,
				'nick': old_player_name,
				'ally.code': new_profile['allyCode'],
				'new.nick': new_player_name,
			})

		for base_id, new_unit in new_roster.items():

			# Handle new units unlocked.
			if base_id not in old_roster:
				messages.append({
					'key': PremiumGuild.MSG_UNIT_UNLOCKED,
					'nick': new_player_name,
					'ally.code': new_profile['allyCode'],
					'unit': base_id,
				})
				continue

			# Handle unit level increase.
			old_level = old_roster[base_id]['level']
			new_level = new_unit['level']
			if old_level < new_level:
				messages.append({
					'key': PremiumGuild.MSG_UNIT_LEVEL,
					'nick': new_player_name,
					'ally.code': new_profile['allyCode'],
					'unit': base_id,
					'level': new_level,
				})

			# Handle unit rarity increase.
			old_rarity = old_roster[base_id]['rarity']
			new_rarity = new_unit['rarity']
			if old_rarity < new_rarity:
				messages.append({
					'key': PremiumGuild.MSG_UNIT_RARITY,
					'nick': new_player_name,
					'ally.code': new_profile['allyCode'],
					'unit': base_id,
					'rarity': new_rarity,
				})

			# Handle gear level increase.
			old_gear_level = old_roster[base_id]['gear']
			new_gear_level = new_unit['gear']
			if old_gear_level < new_gear_level:
				messages.append({
					'key': PremiumGuild.MSG_UNIT_GEAR_LEVEL,
					'nick': new_player_name,
					'ally.code': new_profile['allyCode'],
					'unit': base_id,
					'gear.level': new_gear_level,
				})

			# Handle relic increase.
			old_relic = self.get_relic(old_roster[base_id])
			new_relic = self.get_relic(new_unit)
			if old_relic < new_relic:
				messages.append({
					'key': PremiumGuild.MSG_UNIT_RELIC,
					'nick': new_player_name,
					'ally.code': new_profile['allyCode'],
					'unit': base_id,
					'relic': new_relic,
				})

			# TODO Handle case when there was a gear level change because in that case we need to do things differently
			old_equipped = old_roster[base_id]['equipped']
			new_equipped = new_unit['equipped']
			diff_equipped = [ x for x in new_equipped if x not in old_equipped ]
			if diff_equipped:
				for gear in diff_equipped:
					messages.append({
						'key': PremiumGuild.MSG_UNIT_GEAR_PIECE,
						'nick': new_player_name,
						'ally.code': new_profile['allyCode'],
						'unit': base_id,
						'gear.piece': gear['equipmentId']
					})

			old_skills = { x['id']: x for x in old_roster[base_id]['skills'] }
			new_skills = { x['id']: x for x in new_unit['skills'] }

			for new_skill_id, new_skill in new_skills.items():

				if new_skill_id not in old_skills:
					messages.append({
						'key': PremiumGuild.MSG_UNIT_SKILL_UNLOCKED,
						'nick': new_player_name,
						'ally.code': new_profile['allyCode'],
						'unit': base_id,
						'skill': new_skill_id,
					})
					continue

				old_skill = old_skills[new_skill_id]

				if 'tier' not in old_skill:
					old_skill['tier'] = 0

				if 'tier' not in new_skill:
					new_skill['tier'] = 0

				if old_skill['tier'] < new_skill['tier']:

					messages.append({
						'key': PremiumGuild.MSG_UNIT_SKILL_INCREASED,
						'nick': new_player_name,
						'ally.code': new_profile['allyCode'],
						'unit': base_id,
						'skill': new_skill_id,
						'tier': new_skill['tier']
					})

	def check_diff_player_level(self, guild, old_profile, new_profile, messages):

		new_player_level = new_profile['level']
		old_player_level = old_profile['level']

		if old_player_level < new_player_level:
			messages.append({
				'key': PremiumGuild.MSG_PLAYER_LEVEL,
				'nick': new_profile['name'],
				'ally.code': new_profile['allyCode'],
				'level': new_player_level,
			})

	def check_diff_arena_ranks(self, guild, old_profile, new_profile, messages):

		for arena_type in [ 'char', 'ship' ]:

			old_rank = old_profile['arena'][arena_type]['rank']
			new_rank = new_profile['arena'][arena_type]['rank']

			key = None
			if old_rank < new_rank:
				key = (arena_type == 'char') and PremiumGuild.MSG_ARENA_RANK_DOWN or PremiumGuild.MSG_FLEET_RANK_DOWN

			elif old_rank > new_rank:
				key = (arena_type == 'char') and PremiumGuild.MSG_ARENA_RANK_UP or PremiumGuild.MSG_FLEET_RANK_UP

			if key:
				messages.append({
					'key': key,
					'type': arena_type,
					'nick': new_profile['name'],
					'ally.code': new_profile['allyCode'],
					'old.rank': old_rank,
					'new.rank': new_rank
				})

	def check_last_seen(self, guild, new_profile, messages):

		config = guild.get_config()
		last_seen_max = config[PremiumGuild.MSG_INACTIVITY_MIN]
		last_seen_interval = config[PremiumGuild.MSG_INACTIVITY_REPEAT]

		profile = new_profile
		updated = int(profile['updated'])
		last_sync = datetime.fromtimestamp(updated / 1000)
		delta = datetime.now() - last_sync
		if delta > timedelta(hours=last_seen_max):

			inactivity_key = 'inactivity|%s' % profile['allyCode']
			expire = timedelta(hours=last_seen_interval)

			value = self.redis.get(inactivity_key)
			if value:
				return

			self.redis.setex(inactivity_key, expire, 1)

			last_activity = str(delta - timedelta(microseconds=delta.microseconds))
			messages.append({
				'key': PremiumGuild.MSG_INACTIVITY,
				'nick': profile['name'],
				'ally.code': new_profile['allyCode'],
				'last.seen': last_activity,
			})

	def check_diff(self, guild, old_profile, new_profile):

		messages = []

		self.check_diff_arena_ranks(guild, old_profile, new_profile, messages)

		self.check_diff_player_level(guild, old_profile, new_profile, messages)

		self.check_diff_player_units(guild, old_profile, new_profile, messages)

		self.check_last_seen(guild, new_profile, messages)

		return messages
