#!/usr/bin/env python3

from datetime import datetime, timedelta

import DJANGO
from swgoh.models import BaseUnitSkill, PremiumGuild

class CrawlerDiffer:

	def __init__(self, crawler):
		self.config = crawler.config
		self.logger = crawler.logger
		self.redis = crawler.redis

	def check_diff_player_units(self, guild, old_profile, new_profile, messages):

		old_roster = { x['defId']: x for x in old_profile['roster'] }
		new_roster = { x['defId']: x for x in new_profile['roster'] }

		old_player_name = old_profile['name']
		new_player_name = new_profile['name']
		if old_player_name != new_player_name:
			messages.append({
				'key':       PremiumGuild.MSG_PLAYER_NICK,
				'user':      old_player_name,
				'ally.code': new_profile['allyCode'],
				'new.nick':  new_player_name,
			})

		for base_id, new_unit in new_roster.items():

			# Handle new units unlocked.
			if base_id not in old_roster:
				messages.append({
					'key':       PremiumGuild.MSG_UNIT_UNLOCKED,
					'user':      new_player_name,
					'ally.code': new_profile['allyCode'],
					'unit.id':   base_id,
					'level':     new_unit['level'],
					'gear':      new_unit['gear'],
					'rarity':    new_unit['rarity'],
					'relic':     BaseUnitSkill.get_relic(new_unit),
					'zetas':     BaseUnitSkill.count_zetas(new_unit),
				})
				continue

			# Handle unit level increase.
			old_level = old_roster[base_id]['level']
			new_level = new_unit['level']
			if old_level < new_level:
				messages.append({
					'key':       PremiumGuild.MSG_UNIT_LEVEL,
					'user':      new_player_name,
					'ally.code': new_profile['allyCode'],
					'unit.id':   base_id,
					'level':     new_unit['level'],
					'gear':      new_unit['gear'],
					'rarity':    new_unit['rarity'],
					'relic':     BaseUnitSkill.get_relic(new_unit),
					'zetas':     BaseUnitSkill.count_zetas(new_unit),
				})

			# Handle unit rarity increase.
			old_rarity = old_roster[base_id]['rarity']
			new_rarity = new_unit['rarity']
			if old_rarity < new_rarity:
				messages.append({
					'key':       PremiumGuild.MSG_UNIT_RARITY,
					'user':      new_player_name,
					'ally.code': new_profile['allyCode'],
					'unit.id':   base_id,
					'level':     new_unit['level'],
					'gear':      new_unit['gear'],
					'rarity':    new_unit['rarity'],
					'rarity.new':new_rarity,
					'rarity.old':old_rarity,
					'relic':     BaseUnitSkill.get_relic(new_unit),
					'zetas':     BaseUnitSkill.count_zetas(new_unit),
				})

			# Handle gear level increase.
			old_gear_level = old_roster[base_id]['gear']
			new_gear_level = new_unit['gear']
			if old_gear_level < new_gear_level:
				messages.append({
					'key':       PremiumGuild.MSG_UNIT_GEAR_LEVEL,
					'user':      new_player_name,
					'ally.code': new_profile['allyCode'],
					'unit.id':   base_id,
					'level':     new_unit['level'],
					'gear':      new_unit['gear'],
					'gear.new':  new_gear_level,
					'gear.old':  old_gear_level,
					'rarity':    new_unit['rarity'],
					'relic':     old_gear_level >= 13 and BaseUnitSkill.get_relic(new_unit) or 0,
					'zetas':     BaseUnitSkill.count_zetas(new_unit),
				})

			# Handle relic increase.
			old_relic = BaseUnitSkill.get_relic(old_roster[base_id])
			new_relic = BaseUnitSkill.get_relic(new_unit)
			if old_relic < new_relic:
				messages.append({
					'key':       PremiumGuild.MSG_UNIT_RELIC,
					'user':      new_player_name,
					'ally.code': new_profile['allyCode'],
					'unit.id':   base_id,
					'level':     new_unit['level'],
					'gear':      new_unit['gear'],
					'rarity':    new_unit['rarity'],
					'relic':     new_relic,
					'relic.new': new_relic,
					'relic.old': old_relic,
					'zetas':     BaseUnitSkill.count_zetas(new_unit),
				})

			# TODO Handle case when there was a gear level change because in that case we need to do things differently
			old_equipped = old_roster[base_id]['equipped']
			new_equipped = new_unit['equipped']
			diff_equipped = [ x for x in new_equipped if x not in old_equipped ]
			if diff_equipped:
				for gear in diff_equipped:
					messages.append({
						'key':       PremiumGuild.MSG_UNIT_GEAR_PIECE,
						'user':      new_player_name,
						'ally.code': new_profile['allyCode'],
						'unit.id':   base_id,
						'level':     new_unit['level'],
						'gear':      new_unit['gear'],
						'rarity':    new_unit['rarity'],
						'relic':     BaseUnitSkill.get_relic(new_unit),
						'zetas':     BaseUnitSkill.count_zetas(new_unit),
						'equip.id':  gear['equipmentId'],
					})

			old_skills = { x['id']: x for x in old_roster[base_id]['skills'] }
			new_skills = { x['id']: x for x in new_unit['skills'] }

			for new_skill_id, new_skill in new_skills.items():

				if new_skill_id not in old_skills:
					messages.append({
						'key':       PremiumGuild.MSG_UNIT_SKILL_UNLOCKED,
						'user':      new_player_name,
						'ally.code': new_profile['allyCode'],
						'unit.id':   base_id,
						'level':     new_unit['level'],
						'gear':      new_unit['gear'],
						'rarity':    new_unit['rarity'],
						'relic':     BaseUnitSkill.get_relic(new_unit),
						'zetas':     BaseUnitSkill.count_zetas(new_unit),
						'skill.id':  new_skill_id,
					})
					continue

				old_skill = old_skills[new_skill_id]

				if 'tier' not in old_skill:
					old_skill['tier'] = 0

				if 'tier' not in new_skill:
					new_skill['tier'] = 0

				if old_skill['tier'] < new_skill['tier']:

					new_zetas = BaseUnitSkill.count_zetas(new_unit)
					old_zetas = base_id in old_roster and BaseUnitSkill.count_zetas(old_roster[base_id]) or 0

					messages.append({
						'key':       PremiumGuild.MSG_UNIT_SKILL_INCREASED,
						'user':      new_player_name,
						'ally.code': new_profile['allyCode'],
						'unit.id':   base_id,
						'level':     new_unit['level'],
						'gear':      new_unit['gear'],
						'rarity':    new_unit['rarity'],
						'relic':     BaseUnitSkill.get_relic(new_unit),
						'zetas':     new_zetas,
						'zetas.new': new_zetas,
						'zetas.old': old_zetas,
						'skill.id':  new_skill_id,
						'tier':      new_skill['tier'],
					})

	def check_diff_player_level(self, guild, old_profile, new_profile, messages):

		new_player_level = new_profile['level']
		old_player_level = old_profile['level']

		if old_player_level < new_player_level:
			messages.append({
				'key':       PremiumGuild.MSG_PLAYER_LEVEL,
				'user':      new_profile['name'],
				'ally.code': new_profile['allyCode'],
				'level':     new_player_level,
				'level.new': new_player_level,
				'level.old': old_player_level,
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
					'key':       key,
					'type':      arena_type,
					'user':      new_profile['name'],
					'ally.code': new_profile['allyCode'],
					'rank':      new_rank,
					'rank.new':  new_rank,
					'rank.old':  old_rank,
					# Compat
					'new.rank':  new_rank,
					'old.rank':  old_rank,
				})

	def check_last_seen(self, guild, new_profile, messages):

		config = guild.get_config()
		last_seen_max      = int(config[PremiumGuild.MSG_INACTIVITY_MIN    + '.config'])
		last_seen_interval = int(config[PremiumGuild.MSG_INACTIVITY_REPEAT + '.config'])

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
				'key':       PremiumGuild.MSG_INACTIVITY,
				'user':      profile['name'],
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
