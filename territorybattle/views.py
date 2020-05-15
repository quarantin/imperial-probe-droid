from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt
from collections import OrderedDict
from client import SwgohClient

from .models import TerritoryBattle, TerritoryBattleHistory

import pytz
from datetime import datetime

def ts2date(ts, dateformat='%Y/%m/%d'):
	return datetime.fromtimestamp(int(int(ts) / 1000)).strftime(dateformat)

class TerritoryBattleHistoryView(ListView):

	model = TerritoryBattleHistory
	template_name = 'territorybattle/territorybattlehistory_list.html'
	#template_name = 'territorybattle/tables.html'
	object_list = TerritoryBattleHistory.objects.all()
	queryset = TerritoryBattleHistory.objects.all()

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

		if 'tb' in kwargs:
			filter_kwargs['tb'] = kwargs['tb']

		if 'territory' in kwargs:
			filter_kwargs['territory'] = kwargs['territory']

		if 'activity' in kwargs:
			filter_kwargs['event_type'] = kwargs['activity']

		if 'player' in kwargs:
			filter_kwargs['player_id'] = kwargs['player']

		if 'target' in kwargs:
			filter_kwargs['squad__player_id'] = kwargs['target']

		queryset = self.queryset.filter(**filter_kwargs)

		timezone = kwargs.pop('timezone', 'UTC')

		context['events'] = queryset
		for event in context['events']:
			event.tb = TerritoryBattle.objects.get(id=event.tb_id)
			event.event_type = TerritoryBattleHistory.get_activity_by_num(event.event_type)
			event.timestamp = self.convert_date(event.timestamp, timezone)

		return context

	@csrf_exempt
	def get(self, request, *args, **kwargs):

		context = {}

		if 'tb' in request.GET:
			tb = int(request.GET['tb'])
			kwargs['tb'] = tb
			context['tb'] = tb

		tbs = TerritoryBattle.objects.all()
		if 'tb' not in context:
			tb = tbs and tbs[0].id or None
			kwargs['tb'] = tb
			context['tb'] = tb

		if 'territory' in request.GET:
			territory = request.GET['territory']
			tokens = territory.split('-')
			kwargs['phase'] = tokens[0]
			kwargs['territory'] = tokens[1]
			context['territory'] = territory

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
		players_data = list(TerritoryBattleHistory.objects.values('player_id', 'player_name').distinct())
		for player in sorted(players_data, key=lambda x: x['player_name']):
			id = player['player_id']
			name = player['player_name']
			players[id] = name

		timezones = pytz.common_timezones
		if 'UTC' in timezones:
			timezones.remove('UTC')
		timezones.insert(0, 'UTC')

		context['tbs'] = { x.id: '%s - %s' % (ts2date(x.tb_id), x.get_name()) for x in tbs }

		context['timezones'] = { x: x for x in timezones }

		context['activities'] = { x: y for x, y in TerritoryBattleHistory.EVENT_TYPE_CHOICES }

		#context['territories'] = TerritoryBattleHistory.get_territory_list()

		context['players'] = players

		context['targets'] = players

		return self.render_to_response(context)
