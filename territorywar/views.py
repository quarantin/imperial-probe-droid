from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template.loader import get_template
from django.views.generic import DetailView, ListView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from collections import OrderedDict
from client import SwgohClient

from swgoh.models import Player
import swgoh.views as swgoh_views
from swgoh.views import CsvResponse
from .models import TerritoryWar, TerritoryWarHistory, TerritoryWarSquad, TerritoryWarUnit, TerritoryWarStat

import json
import pytz
from datetime import datetime

from utils import translate

def tw2date(tw, dateformat='%Y/%m/%d'):
	ts = int(str(tw).split(':')[1][1:]) / 1000
	return datetime.fromtimestamp(int(ts)).strftime(dateformat)

class TerritoryWarListView(swgoh_views.ListView):

	def get_context_data(self, request, *args, **kwargs):

		self.object_list = self.get_queryset(*args, **kwargs)

		context = super().get_context_data(*args, **kwargs)

		player = self.get_player(request)
		kwargs['guild'] = player.guild
		context['guild'] = player.guild

		timezone = kwargs.pop('timezone', 'UTC')

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
			#kwargs['activity'] = activity
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
			context['preloaded'] = preloaded

		if 'category' in request.GET:
			category = request.GET.get('category', 'stars')
			kwargs['category'] = category
			context['category'] = category

		self.object_list = self.get_queryset(*args, **kwargs)

		# Has to be called after get_queryset because timezone is not a valid field
		timezone = 'UTC'
		if 'timezone' in request.GET:
			timezone = request.GET['timezone']
			kwargs['timezone'] = timezone
			context['timezone'] = timezone

		context['events'] = self.object_list
		for event in context['events']:
			event.tw = TerritoryWar.objects.get(id=event.tw_id)
			if hasattr(event, 'event_type'):
				event.event_type = TerritoryWarHistory.get_activity_by_num(event.event_type)
			if hasattr(event, 'timestamp'):
				event.timestamp = self.convert_date(event.timestamp, timezone)
			if hasattr(event, 'squad') and event.squad:
				event.target_id = event.squad.player_id
				event.target_name = event.squad.player_name
				event.preloaded = event.squad.is_preloaded
				event.units = []
				units = TerritoryWarUnit.objects.filter(squad=event.squad)
				for unit in units:
					unit_name = translate(unit.base_unit.base_id, language='eng_us')
					event.units.append(unit_name)

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

		context['categories'] = { x: y for x, y in TerritoryWarStat.categories }

		context['players'] = players

		context['targets'] = players

		context['tw_active'] = True

		return context

	@csrf_exempt
	def get(self, request, *args, **kwargs):
		context = self.get_context_data(request, *args, **kwargs)
		return self.render_to_response(context)

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

class TerritoryWarHistoryListView(TerritoryWarListView):

	model = TerritoryWarHistory
	template_name = 'territorywar/territorywarhistory_list.html'
	queryset = TerritoryWarHistory.objects.all()

	def get(self, request, *args, **kwargs):
		context = self.get_context_data(request, *args, **kwargs)
		context['tw_history_active'] = True
		return self.render_to_response(context)


class TerritoryWarHistoryListViewCsv(swgoh_views.ListViewCsv):

	model = TerritoryWarHistory
	queryset = TerritoryWarHistory.objects.all()

	def get_headers(self):
		return [ 'Timestamp', 'Activity', 'Phase', 'Territory', 'Player', 'Score' ]

	def get_object_as_row(self, o):
		return [ o.timestamp, o.event_type, o.phase, o.territory, o.player_name, o.score ]

class TerritoryWarStatListView(TerritoryWarListView):

	model = TerritoryWarStat
	template_name = 'territorywar/territorywarstat_list.html'
	queryset = TerritoryWarStat.objects.all()

	def get(self, request, *args, **kwargs):
		context = self.get_context_data(request, *args, **kwargs)
		context['tw_stats_active'] = True
		return self.render_to_response(context)

class TerritoryWarStatListViewCsv(swgoh_views.ListViewCsv):

	model = TerritoryWarStat
	queryset = TerritoryWarStat.objects.all()

	def get_headers(self):
		return [ 'Category', 'Player', 'Banners']

	def get_object_as_row(self, o):
		return [ o.category, o.player_name, o.player_score ]
