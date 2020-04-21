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
		gear_level = random.randint(1, MAX_GEAR_LEVEL)
		gear = Gear.objects.order_by('?').first()

		msg['ally.code'] = player.ally_code
		msg['gear']      = gear_level
		msg['equip.id']  = gear.base_id
		msg['key']       = key.replace('.format', '')
		msg['last.seen'] = Demo.get_random_last_seen()
		msg['level']     = str(random.randint(1, MAX_LEVEL))
		msg['new.rank']  = str(random.randint(1, 10000))
		msg['user']      = msg['new.nick'] = msg['old.nick'] = player.game_nick
		msg['old.rank']  = str(int(msg['new.rank']) + random.randint(0, 8) * drop)
		msg['rarity']    = str(random.randint(1, MAX_RARITY))
		msg['relics']    = str(random.randint(1, MAX_RELIC))
		msg['zetas']     = str(random.randint(1, 3))
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
