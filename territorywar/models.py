from django.db import models

import json
import pytz
import traceback
from datetime import datetime

from swgoh.models import BaseUnit

import protos.PlayerRpc_pb2 as PlayerRpc

class TerritoryWar(models.Model):

	event_id = models.CharField(max_length=64)

	def __str__(self):
		return str(self.event_id)

	def get_name(self):
		return 'Territory War'

	def get_date(self, dateformat='%Y-%m-%d'):
		ts = int(self.event_id.split(':')[1][1:-3])
		dt = datetime.fromtimestamp(ts)
		return pytz.utc.convert(dt).strftime(dateformat)

	@staticmethod
	def parse(event_id):
		event, created = TerritoryWar.objects.get_or_create(event_id=event_id)
		return event

class  TerritoryWarUnit(models.Model):
	
	squad = models.ForeignKey('TerritoryWarSquad', on_delete=models.CASCADE)
	base_unit = models.ForeignKey(BaseUnit, on_delete=models.CASCADE)
	unit_id = models.CharField(max_length=22)
	role = models.IntegerField()
	unit_level = models.IntegerField()
	unit_gear = models.IntegerField()
	unit_health = models.IntegerField()
	unit_protection = models.IntegerField()
	unit_turn_meter = models.IntegerField()

	@staticmethod
	def parse(squad, unit):

		if 'unitId' not in unit:
			raise Exception('Not a valid unit!')

		try:
			unit_id = unit['unitId']
			o = TerritoryWarUnit.objects.get(unit_id=unit_id)

		except TerritoryWarUnit.DoesNotExist:

			o = TerritoryWarUnit(unit_id=unit_id)

		o.squad = squad

		if 'role' in unit:
			o.role = PlayerRpc.UnitRole.Value(unit['role'])

		if 'baseId' in unit:
			base_id = unit['baseId'].split(':')[0]
			o.base_unit = BaseUnit.objects.get(base_id=base_id)

		if 'stats' in unit:
			stats = unit['stats']

			if 'unitLevel' in stats:
				o.unit_level = stats['unitLevel']

			if 'unitGear' in stats:
				o.unit_gear = stats['unitGear']

		if 'context' in unit:
			context = unit['context']

			if 'health' in context:
				o.unit_health = float(context['health'])

			if 'protection' in context:
				o.unit_protection = float(context['protection'])

			if 'turnMeter' in context:
				o.unit_turn_meter = float(context['turnMeter'])

		o.save()
		return o

class TerritoryWarSquad(models.Model):

	event_id = models.CharField(max_length=22)
	player_id = models.CharField(max_length=22)
	player_name = models.CharField(max_length=64)
	squad_gp = models.IntegerField()

	@staticmethod
	def parse(event_id, squad):

		if 'squad' not in squad or 'units' not in squad['squad']:
			raise Exception('Invalid squad with no units!')

		try:
			o = TerritoryWarSquad.objects.get(event_id=event_id)

		except TerritoryWarSquad.DoesNotExist:

			o = TerritoryWarSquad(event_id=event_id)

		if 'playerId' in squad:
			o.player_id = squad['playerId']

		if 'playerName' in squad:
			o.player_name = squad['playerName']

		if 'squadGp' in squad:
			o.squad_gp = squad['squadGp']

		o.save()

		units = squad['squad']['units']
		for unit in units:
			unit = TerritoryWarUnit.parse(o, unit)

		return o

class TerritoryWarHistory(models.Model):

	ACTIVITY_EMPTY        = (-1, 'Empty')
	ACTIVITY_CONTRIB      = (0, 'Contribution')
	ACTIVITY_CONTRIB_FULL = (1, 'Contribution (Complete)')
	ACTIVITY_DEPLOY       = (2, 'Deploy')
	ACTIVITY_DEPLOY_FLEET = (3, 'Deploy Fleet')
	ACTIVITY_DEPLOY_SQUAD = (4, 'Deploy Squad')
	ACTIVITY_WIN_FLEET    = (5, 'Fleet Win')
	ACTIVITY_WIN_SQUAD    = (6, 'Squad Win')

	ACTIVITY_TYPES = {
		'EMPTY':                                                                       ACTIVITY_EMPTY,
		'TERRITORY_CHANNEL_ACTIVITY_STRIKE_LINKED_CONFLICT_CONTRIBUTION':              ACTIVITY_CONTRIB,
		'TERRITORY_CHANNEL_ACTIVITY_STRIKE_LINKED_CONFLICT_CONTRIBUTION_ALL_COMPLETE': ACTIVITY_CONTRIB_FULL,
		'TERRITORY_CHANNEL_ACTIVITY_CONFLICT_DEFENSE_DEPLOY':                          ACTIVITY_DEPLOY,
		'TERRITORY_CHANNEL_ACTIVITY_CONFLICT_DEFENSE_FLEET_DEPLOY':                    ACTIVITY_DEPLOY_FLEET,
		'TERRITORY_CHANNEL_ACTIVITY_CONFLICT_DEPLOY':                                  ACTIVITY_DEPLOY_SQUAD,
		'TERRITORY_CHANNEL_ACTIVITY_CONFLICT_FLEET_WIN':                               ACTIVITY_WIN_FLEET,
		'TERRITORY_CHANNEL_ACTIVITY_CONFLICT_SQUAD_WIN':                               ACTIVITY_WIN_SQUAD,
	}

	EVENT_TYPE_CHOICES = [
		ACTIVITY_EMPTY,
		ACTIVITY_CONTRIB,
		ACTIVITY_CONTRIB_FULL,
		ACTIVITY_DEPLOY,
		ACTIVITY_DEPLOY_FLEET,
		ACTIVITY_DEPLOY_SQUAD,
		ACTIVITY_WIN_FLEET,
		ACTIVITY_WIN_SQUAD,
	]

	@staticmethod
	def get_activity_by_num(num_activity):
		for num, activity in TerritoryWarHistory.EVENT_TYPE_CHOICES:
			if num == num_activity:
				return activity

		return 'Unknown'

	id = models.CharField(max_length=64, primary_key=True)
	tw = models.ForeignKey(TerritoryWar, on_delete=models.CASCADE)
	timestamp = models.DateTimeField()
	event_type = models.IntegerField(choices=EVENT_TYPE_CHOICES)
	player_id = models.CharField(max_length=22)
	player_name = models.CharField(max_length=64)
	phase = models.IntegerField()
	territory = models.IntegerField()
	score = models.IntegerField(null=True)
	total = models.IntegerField(null=True)
	squad = models.ForeignKey(TerritoryWarSquad, null=True, on_delete=models.CASCADE)

	@staticmethod
	def parse_territory(territory_name):

		tokens = territory_name.split('_') 
		if len(tokens) != 4:
			raise Exception('Invalid data!')

		phase = int(tokens[2][-2:])
		territory = int(tokens[3][-2:])

		return phase, territory

	@staticmethod
	def parse(event):

		to_save_all = []
		try:
			event_id = event['id']
			o = TerritoryWarHistory.objects.get(id=event_id)

		except TerritoryWarHistory.DoesNotExist:

			o = TerritoryWarHistory(id=event_id)

		if 'type' in event:
			if event['type'] != 'TERRITORY_WAR_CONFLICT_ACTIVITY':
				raise Exception('Invalid event type: %s' % event['type'])

		if 'timestamp' in event:
			o.timestamp = event['timestamp']

		if 'playerId' in event:
			o.player_id = event['playerId']

		if 'playerName' in event:
			o.player_name = event['playerName']

		if 'data' in event:
			data = event['data']


			if 'activity' in data:
				activity = data['activity']

				if 'eventId' in activity:
					o.tw = TerritoryWar.parse(activity['eventId'])

				if 'territoryName' in activity:
					phase, territory = TerritoryWarHistory.parse_territory(activity['territoryName'])
					o.phase = phase
					o.territory = territory

				if 'score' in activity:
					o.score = activity['score']

				if 'total' in activity:
					o.total = activity['total']

				if 'details' in activity:
					details = activity['details']

					if 'activityType' in details:
						activity_type = details['activityType']
						o.event_type = TerritoryWarHistory.ACTIVITY_TYPES[activity_type][0]

			if 'squad' in data and 'squad' in data['squad']:
				o.squad = TerritoryWarSquad.parse(event_id, data['squad'])

		o.save()
		return o

	class Meta:
		ordering = ('timestamp',)