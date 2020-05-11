from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt
from client import SwgohClient

from .models import TerritoryWar, TerritoryWarHistory

import json
import pytz
from datetime import datetime

def tw2date(tw, dateformat='%Y/%m/%d'):
	ts = int(str(tw).split(':')[1][1:]) / 1000
	return datetime.fromtimestamp(int(ts)).strftime(dateformat)

class TerritoryWarHistoryView(ListView):

	model = TerritoryWarHistory
	template_name = 'territorywar/territorywarhistory_list.html'
	object_list = TerritoryWarHistory.objects.all()
	queryset = TerritoryWarHistory.objects.all()

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

		if 'tw' in kwargs:
			filter_kwargs['tw'] = kwargs['tw']

		if 'territory' in kwargs:
			filter_kwargs['territory'] = kwargs['territory']

		if 'activity' in kwargs:
			filter_kwargs['event_type'] = kwargs['activity']

		queryset = self.queryset.filter(**filter_kwargs).values()

		timezone = kwargs.pop('timezone', 'UTC')

		context['events'] = queryset
		for event in context['events']:
			print("WTF")
			print(event)
			event['tw'] = TerritoryWar.objects.get(id=event['tw_id'])
			event['event_type'] = TerritoryWarHistory.get_activity_by_num(event['event_type'])
			event['timestamp'] = self.convert_date(event['timestamp'], timezone)

		return context

	@csrf_exempt
	def get(self, request, *args, **kwargs):

		context = {}

		if 'phase' in request.GET:
			phase = int(request.GET['phase'])
			kwargs['phase'] = phase
			context['phase'] = phase

		if 'tw' in request.GET:
			tw = int(request.GET['tw'])
			kwargs['tw'] = tw
			context['tw'] = tw

		if 'territory' in request.GET:
			territory = int(request.GET['territory'])
			kwargs['territory'] = territory
			context['territory'] = territory

		if 'activity' in request.GET:
			activity = int(request.GET['activity'])
			kwargs['activity'] = activity
			context['activity'] = activity

		if 'timezone' in request.GET:
			timezone = request.GET['timezone']
			kwargs['timezone'] = timezone
			context['timezone'] = timezone

		context.update(self.get_context_data(**kwargs))

		tws = TerritoryWar.objects.all()
		timezones = pytz.all_timezones
		if 'UTC' in timezones:
			timezones.remove('UTC')
		timezones.insert(0, 'UTC')

		context['tws'] = { x.id: '%s - %s' % (tw2date(x), x.get_name()) for x in tws }

		context['timezones'] = { x: x for x in timezones }

		context['activities'] = { x: y for x, y in TerritoryWarHistory.EVENT_TYPE_CHOICES }

		context['phases'] = { x: x for x in range(1, 5) }

		return self.render_to_response(context)
