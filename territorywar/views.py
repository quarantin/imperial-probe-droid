from django.shortcuts import render
from django.views.generic import DetailView, ListView
from django.http import HttpResponse, Http404
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from collections import OrderedDict
from client import SwgohClient

import swgoh.views as swgoh_views
from swgoh.models import Player
from swgoh.views import CsvResponse, ListViewCsvMixin, TerritoryEventMixin
from .models import TerritoryWar, TerritoryWarHistory, TerritoryWarSquad, TerritoryWarUnit, TerritoryWarStat

import json
import pytz
from datetime import datetime

from utils import translate

class TerritoryWarMixin(TerritoryEventMixin):

	def event2date(self, tw, dateformat='%Y/%m/%d'):
		ts = int(str(tw).split(':')[1][1:]) / 1000
		return datetime.fromtimestamp(int(ts)).strftime(dateformat)

		return 'tw'

	def get_event(self):

		if 'event' in self.request.GET:
			id = int(self.request.GET['event'])
			return TerritoryWar.objects.get(id=id)

		else:
			print('NO TW IN GET')
			return TerritoryWar.objects.first()

	def get_events(self):
		return { x.id: '%s - %s' % (self.event2date(x.event_id), x.get_name()) for x in TerritoryWar.objects.all() }

	def get_player_list(self, event):

		result = OrderedDict()
		players = list(self.model.objects.filter(event=event).values('player_id', 'player_name').distinct())
		for player in sorted(players, key=lambda x: x['player_name'].lower()):
			id = player['player_id']
			name = player['player_name']
			result[id] = name

		return result

class TerritoryWarListView(TerritoryWarMixin, ListView):

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
			if hasattr(event, 'activity'):
				event.activity = TerritoryWarHistory.get_activity_by_num(event.activity)
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

		context['tws'] = { x.id: '%s - %s' % (event2date(x), x.get_name()) for x in tws }

		context['timezones'] = { x: x for x in timezones }

		context['activities'] = { x: y for x, y in TerritoryWarHistory.ACTIVITY_CHOICES }

		context['territories'] = self.get_territories()

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

class TerritoryWarHistoryListView(TerritoryWarMixin, ListView):

	model = TerritoryWarHistory
	queryset = TerritoryWarHistory.objects.all()

	def get_context_data(self, *args, **kwargs):

		context = super().get_context_data(*args, **kwargs)

		event = self.get_event()
		phase = self.get_phase()
		player = self.get_player()
		target = self.get_target()
		o_player = self.get_player_object()
		activity = self.get_activity()
		territory = self.get_territory()
		preloaded = self.get_preloaded()

		timezone = self.get_timezone()
		timezones = self.get_timezones()

		kwargs['guild'] = o_player.guild
		kwargs['event'] = event

		if activity is not None:
			kwargs['activity'] = activity

		if phase is not None:
			kwargs['phase'] = phase

		if territory is not None:
			tokens = territory.split('-')
			kwargs['phase'] = tokens[0]
			kwargs['territory'] = tokens[1]

		if player is not None:
			kwargs['player_id'] = player

		if target is not None:
			kwargs['squad__player_id'] = target
			context['target'] = target

		if preloaded is not None:
			kwargs['squad__is_preloaded'] = preloaded
			context['preloaded'] = preloaded

		object_list = context['object_list'].filter(**kwargs)

		for o in object_list:
			o.preloaded = o.squad and o.squad.is_preloaded
			if hasattr(o, 'activity'):
				o.activity = TerritoryWarHistory.get_activity_by_num(o.activity)
			if hasattr(o, 'timestamp'):
				o.timestamp = self.convert_date(o.timestamp, timezone)
			if hasattr(o, 'squad') and o.squad:
				o.target_id = o.squad.player_id
				o.target_name = o.squad.player_name
				o.preloaded = o.squad.is_preloaded
				o.units = []
				units = TerritoryWarUnit.objects.filter(squad=o.squad)
				for unit in units:
					unit_name = translate(unit.base_unit.base_id, language='eng_us')
					o.units.append(unit_name)

		context['object_list'] = object_list
		context['event'] = event.id
		context['tw_active'] = True
		context['tw_history_active'] = True
		context['tw'] = event.id
		context['tws'] = self.get_events()
		context['activity'] = activity
		context['activities'] = self.get_activities()
		context['territory'] = territory
		context['territories'] = self.get_territories()
		context['timezones'] = self.get_timezones()
		context['player'] = player
		context['players'] = self.get_player_list(event)
		context['targets'] = context['players']

		return context

	class Meta:
		ordering = [ 'timestamp' ]

class TerritoryWarHistoryListViewCsv(ListViewCsvMixin, TerritoryWarHistoryListView):

	def get_filename(self, event):
		return 'events.csv'

	def get_headers(self):
		return [ 'Timestamp', 'Activity', 'Phase', 'Territory', 'Player', 'Score' ]

	def get_rows(self, o, index):
		return [( o.timestamp, o.activity, o.phase, o.territory, o.player_name, o.score )]

class TerritoryWarStatListView(TerritoryWarMixin, ListView):

	model = TerritoryWarStat
	queryset = TerritoryWarStat.objects.all()

	def get_context_data(self, *args, **kwargs):

		context = super().get_context_data(*args, **kwargs)

		tw = self.get_event()
		player = self.get_player_object()
		category = self.get_category('stars')

		kwargs['guild'] = player.guild
		kwargs['event'] = tw.id

		object_list = context['object_list'].filter(**kwargs)
		for o in object_list:
			o.player_score = o.get_score(category)

		object_list = sorted(object_list, key=lambda o: o.player_name.lower())
		object_list = sorted(object_list, key=lambda o: o.player_score, reverse=True)

		context['object_list'] = object_list
		context['event'] = tw
		context['tw_active'] = True
		context['tw_stats_active'] = True
		context['tw'] = tw.id
		context['tws'] = self.get_events()
		context['category'] = category
		context['categories'] = self.get_categories()

		return context

class TerritoryWarStatListViewCsv(ListViewCsvMixin, TerritoryWarStatListView):

	def get_filename(self, tw):
		tw_date = tw.get_date(dateformat='%Y%m%d')
		tw_name = tw.get_name().replace(' ', '').replace('-', '_')
		return '%s_%s_Contributions.csv' % (tw_date, tw_name)

	def get_headers(self):
		return [ 'Category', 'Player', 'Banners']

	def get_rows(self, o, index):

		rows = []

		for category, category_name in TerritoryWarStat.categories:
			rows.append(( category, o.player_name, o.get_score(category) ))

		return rows
