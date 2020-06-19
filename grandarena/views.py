import pytz

from django.shortcuts import render
from django.core import serializers
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt

from collections import OrderedDict
from client import SwgohClient

from .models import GrandArena, GrandArenaHistory

class GrandArenaHistoryView(ListView):

	model = GrandArenaHistory
	template_name = 'grandarena/grandarenahistory_list.html'
	object_list = GrandArenaHistory.objects.all()
	queryset = GrandArenaHistory.objects.all()

	def get_queryset(self):
		return self.queryset

	def convert_date(self, utc_date, timezone):

		local_tz = pytz.timezone(timezone)
		local_dt = utc_date.astimezone(local_tz)

		return local_tz.normalize(local_dt).strftime('%Y-%m-%d %H:%M:%S')

	def get_context_data(self, **kwargs):

		context = super().get_context_data(**kwargs)

		filter_kwargs = {}

		if 'phase' in kwargs:
			filter_kwargs['phase'] = kwargs['phase']

		if 'ga' in kwargs:
			filter_kwargs['ga'] = kwargs['ga']

		if 'territory' in kwargs:
			filter_kwargs['territory'] = kwargs['territory']

		if 'activity' in kwargs:
			filter_kwargs['activity'] = kwargs['activity']

		if 'player' in kwargs:
			filter_kwargs['player_id'] = kwargs['player']

		if 'target' in kwargs:
			filter_kwargs['squad__player_id'] = kwargs['target']

		queryset = self.queryset.filter(**filter_kwargs)

		timezone = kwargs.pop('timezone', 'UTC')

		context['events'] = queryset
		for event in context['events']:
			event.ga = GrandArena.objects.get(id=event.ga_id)
			event.activity = GrandArenaHistory.get_activity_by_num(event.activity)
			event.timestamp = self.convert_date(event.timestamp, timezone)
			"""
			try:
				target = GrandArenaSquad.objects.get(event_id=event.id)
				event.target_id = target.player_id
				event.target_name = target.player_name
			except GrandArenaSquad.DoesNotExist:
				pass
			"""

		return context

	@csrf_exempt
	def get(self, request, *args, **kwargs):

		context = {}

		if 'ga' in request.GET:
			ga = int(request.GET['ga'])
			kwargs['ga'] = ga
			context['ga'] = ga

		gas = GrandArena.objects.all()
		if 'ga' not in context:
			ga = gas and gas[0].id or None
			kwargs['ga'] = ga
			context['ga'] = ga

		if 'territory' in request.GET:
			territory = request.GET['territory']
			tokens = territory.split('-')
			kwargs['phase'] = tokens[0]
			kwargs['territory'] = tokens[1]
			context['territory'] = territory
			print('WTF1: %s' % context['territory'])

		if 'activity' in request.GET:
			activity = int(request.GET['activity'])
			kwargs['activity'] = activity
			context['activity'] = activity

		if 'timezone' in request.GET:
			timezone = request.GET['timezone']
			kwargs['timezone'] = timezone
			context['timezone'] = timezone

		if 'player' in request.GET:
			player = request.GET['player']
			kwargs['player'] = player
			context['player'] = player

		if 'target' in request.GET:
			target = request.GET['target']
			kwargs['target'] = target
			context['target'] = target

		context.update(self.get_context_data(**kwargs))

		# We have to do this after context.update() because it will override territory
		if 'territory' in request.GET:
			context['territory'] = request.GET['territory']

		players = OrderedDict()
		#players_data = list(GrandArenaSquad.objects.values('player_id', 'player_name').distinct())
		#for player in sorted(players_data, key=lambda x: x['player_name']):
		#	id = player['player_id']
		#	name = player['player_name']
		#	players[id] = name

		timezones = pytz.common_timezones
		if 'UTC' in timezones:
			timezones.remove('UTC')
		timezones.insert(0, 'UTC')

		context['gas'] = { x.id: '%s - %s' % (ga2date(x), x.get_name()) for x in gas }

		context['timezones'] = { x: x for x in timezones }

		#context['activities'] = { x: y for x, y in GrandArenaHistory.ACTIVITY_CHOICES }

		#context['territories'] = GrandArenaHistory.get_territory_list()

		context['players'] = players

		context['targets'] = players

		return self.render_to_response(context)
