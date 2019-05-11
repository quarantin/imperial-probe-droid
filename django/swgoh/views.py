from django.shortcuts import render
from django.http import JsonResponse 

from .models import Player, BaseUnitGear, Translation

import json

def gear_levels(request, base_id, ally_code):

	result = {}
	language = 'eng_us'

	try:
		player = Player.objects.get(ally_code=ally_code)
		language = player.language

	except Player.DoesNotExist:
		player = None

	gear_levels = BaseUnitGear.get_unit_gear_levels(base_id)
	for gear_level in gear_levels:
		unit_name = gear_level.unit.name
		if unit_name not in result:
			result[unit_name] = {
				'url': gear_level.unit.get_url(),
				'tiers': {},
			}

		tier = gear_level.tier
		if tier not in result[unit_name]['tiers']:
			result[unit_name]['tiers'][tier] = {}

		slot = gear_level.slot
		gear_name = gear_level.gear.name

		try:
			t = Translation.objects.get(string_id=gear_level.gear.base_id, language=language)
			gear_name = t.translation

		except Translation.DoesNotExist:
			pass

		result[unit_name]['tiers'][tier][slot] = {
			'gear': gear_name,
			'url': gear_level.gear.get_url(),
		}

	return JsonResponse(result)
