from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template

#from .forms import AllyCodeForm

from client import SwgohClient

import json

from asgiref.sync import async_to_sync

def parse_json():

	fin = open('tb-events-20200507-now.json', 'r')
	events = json.loads(fin.read())
	fin.close()

	result = {}
	for event in events:
		typ = event['type']
		if typ not in result:
			result[typ] = []

		if 'zone' in event:
			event['zone'] = event['zone'].replace('geonosis_separatist_', '')

		result[typ].append(event)

	return result

@async_to_sync
async def index(request):

	ctx = {}

	events = parse_json()
	ctx['types'] = events

	return render(request, 'territorybattle/index.html', ctx)
