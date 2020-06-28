from django.shortcuts import render
from django.views.generic.list import ListView
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

import swgoh.views as swgoh_views
from swgoh.models import Player
from swgoh.views import CsvResponse, ListViewCsvMixin, TerritoryEventMixin
from .models import TerritoryBattle, TerritoryBattleHistory, TerritoryBattleStat

import pytz
from datetime import datetime

class TerritoryBattleHistoryListView(TerritoryEventMixin, ListView):

	model = TerritoryBattleHistory
	event_model = TerritoryBattle
	queryset = TerritoryBattleHistory.objects.all()

	def get_context_data(self, *args, **kwargs):

		context = super().get_context_data(*args, **kwargs)

		event = self.get_event()
		phase = self.get_phase()
		player = self.get_player()
		o_player = self.get_player_object()
		activity = self.get_activity()
		territory = self.get_territory()

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

		context['object_list'] = context['object_list'].filter(**kwargs)
		context['event'] = event
		context['tb_active'] = True
		context['tb_history_active'] = True
		context['tb'] = event.id
		context['tbs'] = self.get_events()
		context['activity'] = activity
		context['activities'] = self.get_activities()
		context['territory'] = territory
		context['territories'] = self.get_territories(event.tb_type)
		context['timezone'] = timezone
		context['timezones'] = timezones
		context['player'] = player
		context['players'] = self.get_player_list(event)

		return context

class TerritoryBattleHistoryListViewCsv(TerritoryBattleHistoryListView, ListViewCsvMixin):

	def get_filename(self, tb):
		tb_date = tb.get_date(dateformat='%Y%m%d')
		tb_name = tb.get_name().replace(' ', '').replace('-', '_')
		return '%s_TerritoryBattle_%s_History.csv' % (tb_date, tb_name)

	def get_headers(self):
		return ('Timestamp', 'Activity', 'Territory', 'Player', 'Score')

	def get_rows(self, o, index):
		return [( o.timestamp, o.get_activity_display(), o.get_territory(), o.player_name, o.score )]

class TerritoryBattleStatListView(TerritoryEventMixin, ListView):

	model = TerritoryBattleStat
	event_model = TerritoryBattle
	queryset = TerritoryBattleStat.objects.all()

	def get_context_data(self, *args, **kwargs):

		context = super().get_context_data(*args, **kwargs)

		tb = self.get_event()
		player = self.get_player_object()
		category = self.get_category('summary')

		kwargs['guild'] = player.guild
		kwargs['event'] = tb.id

		object_list = context['object_list'].filter(**kwargs)
		for o in object_list:
			o.player_score = o.get_score(category)

		object_list = sorted(object_list, key=lambda o: o.player_name.lower())
		object_list = sorted(object_list, key=lambda o: o.player_score, reverse=True)

		context['object_list'] = object_list
		context['event'] = tb
		context['tb_active'] = True
		context['tb_stats_active'] = True
		context['tb'] = tb.id
		context['tbs'] = self.get_events()
		context['category'] = category
		context['categories'] = self.get_categories()

		return context

class TerritoryBattleStatListViewCsv(TerritoryBattleStatListView, ListViewCsvMixin):

	def get_filename(self, tb):
		tb_date = tb.get_date(dateformat='%Y%m%d')
		tb_name = tb.get_name().replace(' ', '').replace('-', '_')
		return '%s_TerritoryBattle_%s_Contributions.csv' % (tb_date, tb_name)

	def get_headers(self):
		return ('Category', 'Player', 'Banners')

	def get_rows(self, o, index):

		rows = []

		for category, category_name in TerritoryBattleStat.categories:
			rows.append(( category, o.player_name, o.get_score(category) ))

		return rows
