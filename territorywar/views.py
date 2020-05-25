from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template.loader import get_template
from django.views.generic import DetailView, ListView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from collections import OrderedDict
from client import SwgohClient

from swgoh.models import Player
from .models import TerritoryWar, TerritoryWarHistory, TerritoryWarSquad, TerritoryWarUnit

import json
import pytz
from datetime import datetime

from utils import translate

def tw2date(tw, dateformat='%Y/%m/%d'):
	ts = int(str(tw).split(':')[1][1:]) / 1000
	return datetime.fromtimestamp(int(ts)).strftime(dateformat)

class TerritoryWarSquadView(DetailView):

	model = TerritoryWarSquad
	template_name = 'territorywar/territorywarsquad_detail.html'

	def get_object(self, *args, **kwargs):

		if 'event_id' in kwargs:

			try:
				return TerritoryWarSquad.objects.get(event_id=kwargs['event_id'])

			except:
				pass

		raise Http404('No such squad')

	def get_context_data(self, **kwargs):

		context = super().get_context_data(**kwargs)

		context['units'] = list(TerritoryWarUnit.objects.filter(squad=self.object))
		for unit in context['units']:
			unit.name = translate(unit.base_unit.base_id, language='eng_us')

		return context

	def get(self, request, *args, **kwargs):

		self.object = self.get_object(*args, **kwargs)

		context = self.get_context_data(**kwargs)

		return self.render_to_response(context)

class TerritoryWarHistoryView(ListView):

	model = TerritoryWarHistory
	template_name = 'territorywar/territorywarhistory_list.html'
	queryset = TerritoryWarHistory.objects.all()

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

		queryset = self.get_queryset(**kwargs)

		context['events'] = queryset
		for event in context['events']:
			event.tw = TerritoryWar.objects.get(id=event.tw_id)
			event.event_type = TerritoryWarHistory.get_activity_by_num(event.event_type)
			event.timestamp = self.convert_date(event.timestamp, timezone)
			try:
				target = TerritoryWarSquad.objects.get(event_id=event.id)
				event.target_id = target.player_id
				event.target_name = target.player_name
				event.squad = target
				event.units = target.get_units_names(language='eng_us')
				event.preloaded = target.is_preloaded
			except TerritoryWarSquad.DoesNotExist:
				pass

		return context

	@csrf_exempt
	def get(self, request, *args, **kwargs):

		context = {}

		player = self.get_player(request)
		kwargs['guild_id'] = player.guild.id
		context['guild_id'] = player.guild.id

		if 'tw' in request.GET:
			tw = int(request.GET['tw'])
			kwargs['tw'] = tw
			context['tw'] = tw

		tws = TerritoryWar.objects.all()
		if 'tw' not in context:
			tw = tws and tws[0].id or None
			kwargs['tw'] = tw
			context['tw'] = tw

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
			kwargs['player_id'] = player
			context['player'] = player

		if 'target' in request.GET:
			target = request.GET['target']
			kwargs['squad__player_id'] = target
			context['target'] = target

		if 'preloaded' in request.GET:
			preloaded = (request.GET['preloaded'].lower() == 'yes') and 1 or 0
			kwargs['squad__is_preloaded'] = preloaded
			kwargs['preloaded'] = preloaded
			context['preloaded'] = preloaded

		self.object_list = self.get_queryset(*args, **kwargs)

		# Has to be called after get_queryset becaue timezone is not a valid field
		if 'timezone' in request.GET:
			timezone = request.GET['timezone']
			kwargs['timezone'] = timezone
			context['timezone'] = timezone

		context.update(self.get_context_data(*args, **kwargs))

		# We have to do this after context.update() because it will override territory
		if 'territory' in request.GET:
			context['territory'] = request.GET['territory']

		players = OrderedDict()
		players_data = list(TerritoryWarSquad.objects.values('player_id', 'player_name').distinct())
		for player in sorted(players_data, key=lambda x: x['player_name']):
			id = player['player_id']
			name = player['player_name']
			players[id] = name

		timezones = pytz.common_timezones
		if 'UTC' in timezones:
			timezones.remove('UTC')
		timezones.insert(0, 'UTC')

		context['tws'] = { x.id: '%s - %s' % (tw2date(x), x.get_name()) for x in tws }

		context['timezones'] = { x: x for x in timezones }

		context['activities'] = { x: y for x, y in TerritoryWarHistory.EVENT_TYPE_CHOICES }

		context['territories'] = TerritoryWarHistory.get_territory_list()

		context['players'] = players

		context['targets'] = players

		return self.render_to_response(context)
