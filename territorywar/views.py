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

class TerritoryWarHistoryListView(TerritoryEventMixin, ListView):

	model = TerritoryWarHistory
	event_model = TerritoryWar
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
			if hasattr(o, 'timestamp') and o.timestamp:
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
		context['event'] = event
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

	def get_filename(self, tw):
		tw_date = tw.get_date(dateformat='%Y%m%d')
		tw_name = tw.get_name().replace(' ', '').replace('-', '_')
		return '%s_%s_History.csv' % (tw_date, tw_name)

	def get_headers(self):
		return [ 'Timestamp', 'Activity', 'Territory', 'Player', 'Score' ]

	def get_rows(self, o, index):
		return [( o.timestamp, o.get_activity_display(), o.get_territory(), o.player_name, o.score )]

class TerritoryWarStatListView(TerritoryEventMixin, ListView):

	model = TerritoryWarStat
	event_model = TerritoryWar
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
