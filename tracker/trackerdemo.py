#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import random
from datetime import datetime, timedelta

from constants import *

import DJANGO
from swgoh.models import BaseUnit, BaseUnitSkill, Gear, PremiumGuild

class Demo:

	tokens = [
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
	]

	def get_random_value(author, token):

		if token == 'gear.level.roman':
			gear = random.randint(1, MAX_GEAR_LEVEL)
			return ROMAN[gear]

		if token == 'gear.piece':
			return Gear.objects.order_by('?').first().base_id

		if token == 'last.seen':
			days = random.randint(1, 15)
			return str((datetime.now() - timedelta(days=days)))

		if token == 'level':
			return str(random.randint(1, MAX_LEVEL))

		if token in [ 'nick', 'new.nick', 'old.nick' ]:
			return author.display_name

		if token in [ 'new.rank', 'old.rank' ]:
			return str(random.randint(1, 10000))

		if token == 'unit':
			return BaseUnit.objects.filter(combat_type=1).order_by('?').first().base_id

		if token == 'rarity':
			return str(random.randint(1, MAX_RARITY))

		if token == 'relic':
			return str(random.randint(1, MAX_RELIC))

		if token == 'skill':
			return BaseUnitSkill.objects.order_by('?').first().skill_id

		if token == 'tier':
			return str(random.randint(1, MAX_SKILL_TIER))

		raise Exception('Unsupported Demo Handler for token: %s' % token)

	def get_random_messages(author, pref_key):

		msgs = []

		if pref_key is None:
			pref_key = 'all'

		lkey = pref_key.lower()
		for key in PremiumGuild.MESSAGE_FORMATS:

			if lkey != 'all' and lkey not in key:
				continue

			msg = PremiumGuild.MESSAGE_FORMATS[key]
			for token in Demo.tokens:
				strtoken = '${%s}' % token
				if strtoken in msg:
					msg = msg.replace(strtoken, Demo.get_random_value(author, token))

			msgs.append(msg)

		return msgs
