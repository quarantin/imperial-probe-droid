#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import json
import random
from datetime import datetime, timedelta

from constants import *
from utils import translate

import DJANGO
from swgoh.models import BaseUnit, BaseUnitSkill, Gear, Player, PremiumGuild

class Demo:

	def get_random_last_seen():
		days = random.randint(1, 15)
		hours = random.randint(0, 23)
		minutes = random.randint(0, 59)
		now = datetime.now()
		delta = now - (now - timedelta(days=days, hours=hours, minutes=minutes))
		last_seen = delta - timedelta(microseconds=delta.microseconds)
		return str(last_seen)

	def get_random_message(author, key):

		msg = {}

		drop = key.endswith('.down.format') and -1 or 1

		player = random.choice(Player.objects.filter(discord_id=author.id))
		unit = BaseUnit.objects.filter(combat_type=1).order_by('?').first()
		equip = Gear.objects.order_by('?').first()

		gear_level = random.randint(2, MAX_GEAR_LEVEL)
		new_gear = gear_level
		old_gear = gear_level - 1

		relic = random.randint(1, MAX_RELIC)
		new_relic = str(relic)
		old_relic = str(relic - 1)

		rarity = random.randint(1, MAX_RARITY)
		new_rarity = str(rarity)
		old_rarity = str(rarity - 1)

		rank = random.randint(1, 10000)
		new_rank = str(rank)
		old_rank = str(rank + random.randint(0, 8) * drop)

		level = random.randint(1, MAX_LEVEL)
		new_level = str(level)
		old_level = str(level - 1)

		zetas = random.randint(1, 3)
		new_zetas = str(zetas)
		old_zetas = str(zetas - 1)

		msg['ally.code'] = player.ally_code
		msg['gear']      = new_gear
		msg['gear.new']  = new_gear
		msg['gear.old']  = old_gear
		msg['equip.id']  = equip.base_id
		msg['key']       = key.replace('.format', '')
		msg['last.seen'] = Demo.get_random_last_seen()
		msg['level']     = new_level
		msg['level.new'] = new_level
		msg['level.old'] = old_level
		msg['new.rank']  = new_rank
		msg['rank.new']  = new_rank
		msg['old.rank']  = old_rank
		msg['rank.old']  = old_rank
		msg['user']      = msg['new.nick'] = msg['old.nick'] = player.player_name
		msg['rarity']    = new_rarity
		msg['rarity.new']= new_rarity
		msg['rarity.old']= old_rarity
		msg['relic']     = new_relic
		msg['relic.new'] = new_relic
		msg['relic.old'] = old_relic
		msg['zetas']     = new_zetas
		msg['zetas.new'] = new_zetas
		msg['zetas.old'] = old_zetas
		msg['skill.id']  = BaseUnitSkill.objects.filter(unit=unit).order_by('?').first().skill_id
		msg['tier']      = str(random.randint(1, MAX_SKILL_TIER))
		msg['unit.id']   = unit.base_id

		return msg

	def get_random_messages(bot, ctx, config, pref_key):

		msgs = []
		dicts = []

		if pref_key is None:
			pref_key = 'all'

		lkey = pref_key.lower()
		for key, fmt in config.items():

			if lkey != 'all' and lkey not in key or not key.endswith('.format'):
				continue

			msg = Demo.get_random_message(ctx.author, key)
			bot.prepare_message(ctx.message.channel.guild, config, msg)
			final_msg = bot.format_message(msg, fmt)
			msgs.append(final_msg)
			dicts.append(msg)

		return msgs, dicts
