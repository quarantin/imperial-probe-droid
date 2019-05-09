from django.shortcuts import render
from django.http import JsonResponse 

from .models import BaseUnitGear

import json

def gear_levels(request, base_id):
	gear_levels = BaseUnitGear.get_unit_gear_levels(base_id)
	result = {}

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
		result[unit_name]['tiers'][tier][slot] = {
			'gear': gear_level.gear.name,
			'url': gear_level.gear.get_url(),
		}

	return JsonResponse(result)
