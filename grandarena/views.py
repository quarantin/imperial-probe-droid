from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template

from .forms import AllyCodeForm

from client import SwgohClient

import json

from asgiref.sync import async_to_sync

@async_to_sync
async def index(request):

	ctx = {}

	if request.method == 'POST':

		form = AllyCodeForm(request.POST)

		if form.is_valid():
			data = request.POST.copy()
			client = SwgohClient()
			profile = await client.get_player_profile(ally_code=data['ally_code'])
			print(json.dumps(profile, indent=4))

	else:
		form = AllyCodeForm()

	ctx['form'] = form

	return render(request, 'grandarena/index.html', ctx)
