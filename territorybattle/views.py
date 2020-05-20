from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator

from collections import OrderedDict
from client import SwgohClient

from swgoh.models import Player
from .models import TerritoryBattle, TerritoryBattleHistory

import pytz
from datetime import datetime

def ts2date(tb, dateformat='%Y/%m/%d'):
	print(tb)
	ts = int(str(tb).split(':')[1][1:]) / 1000
	return datetime.fromtimestamp(int(ts)).strftime(dateformat)

class TerritoryBattleHistoryView(ListView):

	model = TerritoryBattleHistory
	template_name = 'territorybattle/territorybattlehistory_list.html'
	queryset = TerritoryBattleHistory.objects.all()

	def get_player(self, request):

		user = request.user
		if not user.is_authenticated:
			user = User.objects.get(id=2)

		try:
			return Player.objects.get(user=user)

		except Player.DoesNotExist:
			return None

	def get_queryset(self, *args, **kwargs):
		return self.queryset.filter(**kwargs)

	def convert_date(self, utc_date, timezone):

		local_tz = pytz.timezone(timezone)
		local_dt = utc_date.astimezone(local_tz)

		return local_tz.normalize(local_dt).strftime('%Y-%m-%d %H:%M:%S')

	def get_context_data(self, *args, **kwargs):

		timezone = kwargs.pop('timezone', 'UTC')

		context = super().get_context_data(*args, **kwargs)

		queryset = self.get_queryset(*args, **kwargs)

		context['events'] = queryset
		for event in context['events']:
			event.tb = TerritoryBattle.objects.get(id=event.tb_id)
			event.event_type = TerritoryBattleHistory.get_activity_by_num(event.event_type)
			event.timestamp = self.convert_date(event.timestamp, timezone)

		return context

	def get(self, request, *args, **kwargs):

		context = {}

		player = self.get_player(request)
		kwargs['guild'] = player.guild
		context['guild'] = player.guild

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
			kwargs['event_type'] = activity
			kwargs['activity'] = activity
			context['activity'] = activity

		if 'player' in request.GET:
			player = request.GET['player']
			kwargs['player'] = player
			context['player'] = player

		if 'target' in request.GET:
			target = request.GET['target']
			kwargs['squad__player_id'] = target
			kwargs['target'] = target
			context['target'] = target

		self.object_list = self.get_queryset(*args, **kwargs)

		# Has to be called after get_queryset because timezone is not a valid field
		if 'timezone' in request.GET:
			timezone = request.GET['timezone']
			kwargs['timezone'] = timezone
			context['timezone'] = timezone

		context.update(self.get_context_data(*args, **kwargs))

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

		context['tbs'] = { x.id: '%s - %s' % (ts2date(x.event_id), x.get_name()) for x in tbs }

		context['timezones'] = { x: x for x in timezones }

		context['activities'] = { x: y for x, y in TerritoryBattleHistory.EVENT_TYPE_CHOICES }

		#context['territories'] = TerritoryBattleHistory.get_territory_list()

		context['players'] = players

		context['targets'] = players

		return self.render_to_response(context)
