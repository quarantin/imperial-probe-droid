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

	tokens = {
		'gear.level.roman',
		'gear.piece',
		'last.seen',
		'level',
		'new.nick',
		'new.rank',
		'nick',
		'old.rank',
		'rarity',
		'relic',
		'skill',
		'tier',
		'unit',
		'unit.id',
	}

	def get_random_message(author):

		msg = {}

		days = random.randint(1, 15)
		hours = random.randint(0, 23)
		minutes = random.randint(0, 59)
		now = datetime.now()
		delta = now - (now - timedelta(days=days, hours=hours, minutes=minutes))
		last_seen = delta - timedelta(microseconds=delta.microseconds)

		player = random.choice(Player.objects.filter(discord_id=author.id))
		unit = BaseUnit.objects.filter(combat_type=1).order_by('?').first()
		gear_level = random.randint(1, MAX_GEAR_LEVEL)
		gear = Gear.objects.order_by('?').first()

		msg['ally.code']        = player.ally_code
		msg['gear.level']       = gear_level
		msg['gear.level.roman'] = ROMAN[gear_level]
		msg['gear.piece']       = gear.base_id
		msg['key']              = random.choice([ x[0] for x in PremiumGuild.MESSAGE_DEFAULTS ])
		msg['last.seen']        = str(last_seen)
		msg['level']            = str(random.randint(1, MAX_LEVEL))
		msg['nick']             = msg['new.nick'] = msg['old.nick'] = player.game_nick
		msg['new.rank']         = str(random.randint(1, 10000))
		msg['old.rank']         = str(random.randint(1, 10000))
		msg['rarity']           = str(random.randint(1, MAX_RARITY))
		msg['relic']            = str(random.randint(1, MAX_RELIC))
		msg['skill']            = BaseUnitSkill.objects.filter(unit=unit).order_by('?').first().skill_id
		msg['tier']             = str(random.randint(1, MAX_SKILL_TIER))
		msg['unit']             = unit.base_id

		return msg

	def get_random_messages(bot, ctx, config, pref_key):

		msgs = []

		if pref_key is None:
			pref_key = 'all'

		lkey = pref_key.lower()
		for key, fmt in config.items():

			if lkey != 'all' and lkey not in key or not key.endswith('.format'):
				continue

			msg = Demo.get_random_message(ctx.author)
			bot.prepare_message(ctx.message.channel.guild, config, msg)
			final_msg = bot.format_message(msg, fmt)
			msgs.append(final_msg)

		return msgs
