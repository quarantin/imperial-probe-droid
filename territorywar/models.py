from django.db import models, transaction

from swgoh.models import BaseUnit, Guild

import protos.PlayerRpc_pb2 as PlayerRpc

import pytz
from datetime import datetime

class TerritoryWar(models.Model):

	event_id = models.CharField(max_length=64)
	timestamp = models.DateTimeField()

	def __str__(self):
		return '%s - %s' % (self.get_name(), self.get_date())

	def get_name(self):
		return 'Territory War'

	def get_date(self, dateformat='%Y-%m-%d'):
		ts = int(self.event_id.split(':')[1][1:-3])
		dt = datetime.fromtimestamp(ts, tz=pytz.utc)
		return dt.strftime(dateformat)

	@staticmethod
	def parse(event_id):
		ts = int(event_id.split(':')[1][1:-3])
		timestamp = datetime.fromtimestamp(ts, tz=pytz.utc)
		event, created = TerritoryWar.objects.get_or_create(event_id=event_id, timestamp=timestamp)
		return event

	class Meta:
		ordering = ('-timestamp',)

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
	is_preloaded = models.BooleanField(default=False)

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

		o.is_preloaded = False

		if 'context' in unit:
			context = unit['context']

			if 'health' in context:
				o.unit_health = float(context['health'])
				if o.unit_health != 100:
					o.is_preloaded = True

			if 'protection' in context:
				o.unit_protection = float(context['protection'])
				if o.unit_protection != 100:
					o.is_preloaded = True

			if 'turnMeter' in context:
				o.unit_turn_meter = float(context['turnMeter'])
				if o.unit_turn_meter != 0:
					o.is_preloaded = True

			# If the unit is dead (0 health) then we don't count it as preloading
			if 'health' in context and float(context['health']) == 0:
				o.is_preloaded = False

		o.save()
		return o

	def get_name(self, language='eng_us'):
		from utils import translate
		return translate(self.base_unit.base_id, language=language)

class TerritoryWarSquad(models.Model):

	event_id = models.CharField(max_length=22)
	player_id = models.CharField(max_length=22)
	player_name = models.CharField(max_length=64)
	squad_gp = models.IntegerField()
	is_preloaded = models.BooleanField(default=False)

	@staticmethod
	def parse(event_id, activity, squad):

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

		o.is_preloaded = False
		o.save()

		units = squad['squad']['units']
		for unit in units:
			unit = TerritoryWarUnit.parse(o, unit)
			if unit.is_preloaded:
				o.is_preloaded = True

		if activity in [ TerritoryWarHistory.ACTIVITY_WIN_FLEET[0], TerritoryWarHistory.ACTIVITY_WIN_SQUAD[0] ]:
			o.is_preloaded = False

		o.save()
		return o

	def get_units(self):
		return list(TerritoryWarUnit.objects.filter(squad=self))

	def get_units_names(self, language='eng_us'):
		names = []
		units = self.get_units()
		for unit in units:
			names.append(unit.get_name(language=language))

		return names

class TerritoryWarHistory(models.Model):

	ACTIVITY_EMPTY        = (1, 'Battle Start')
	ACTIVITY_DEPLOY       = (2, 'Deploy')
	ACTIVITY_DEPLOY_FLEET = (3, 'Deploy Fleet')
	ACTIVITY_WIN_FLEET    = (4, 'Fleet Win')
	ACTIVITY_WIN_SQUAD    = (5, 'Squad Win')

	ACTIVITY_TYPES = {
		'EMPTY':                                                    ACTIVITY_EMPTY,
		'TERRITORY_CHANNEL_ACTIVITY_CONFLICT_DEFENSE_DEPLOY':       ACTIVITY_DEPLOY,
		'TERRITORY_CHANNEL_ACTIVITY_CONFLICT_DEFENSE_FLEET_DEPLOY': ACTIVITY_DEPLOY_FLEET,
		'TERRITORY_CHANNEL_ACTIVITY_CONFLICT_FLEET_WIN':            ACTIVITY_WIN_FLEET,
		'TERRITORY_CHANNEL_ACTIVITY_CONFLICT_SQUAD_WIN':            ACTIVITY_WIN_SQUAD,
	}

	ACTIVITY_CHOICES = [
		ACTIVITY_EMPTY,
		ACTIVITY_DEPLOY,
		ACTIVITY_DEPLOY_FLEET,
		ACTIVITY_WIN_FLEET,
		ACTIVITY_WIN_SQUAD,
	]

	TERRITORIES = {
		1: {
			1: 'Top 1',
			2: 'Bottom 1',
		},
		2: {
			1: 'Top 2',
			2: 'Bottom 2',
		},
		3: {
			1: 'Top 3',
			2: 'Middle 3',
			3: 'Bottom 3',
		},
		4: {
			1: 'Top 4',
			2: 'Middle 4',
			3: 'Bottom 4',
		},
	}

	@staticmethod
	def get_activity_by_num(num_activity):
		for num, activity in TerritoryWarHistory.ACTIVITY_CHOICES:
			if num == num_activity:
				return activity

		return 'Unknown'

	eid = models.CharField(max_length=64)
	guild = models.ForeignKey(Guild, on_delete=models.CASCADE, null=True)
	event = models.ForeignKey(TerritoryWar, on_delete=models.CASCADE)
	timestamp = models.DateTimeField()
	activity = models.IntegerField(choices=ACTIVITY_CHOICES)
	player_id = models.CharField(max_length=22)
	player_name = models.CharField(max_length=64)
	phase = models.IntegerField()
	territory = models.IntegerField()
	score = models.IntegerField(null=True)
	total = models.IntegerField(null=True)
	squad = models.ForeignKey(TerritoryWarSquad, null=True, on_delete=models.CASCADE)

	def get_territory(self):
		return TerritoryWarHistory.TERRITORIES[self.phase][self.territory]

	@staticmethod
	def get_territory_list(tb_type=None):

		territory_list = {}
		for phase, territories in TerritoryWarHistory.TERRITORIES.items():
			for territory, name in territories.items():
				key = '%d-%d' % (phase, territory)
				territory_list[key] = name

		return territory_list

	@staticmethod
	def parse_territory(territory_name):

		tokens = territory_name.split('_') 
		if len(tokens) != 4:
			raise Exception('Invalid data!')

		phase = int(tokens[2][-2:])
		territory = int(tokens[3][-2:])

		return phase, territory

	@staticmethod
	def parse(guild, event):

		created = True
		to_save_all = []
		try:
			event_id = event['id']
			o = TerritoryWarHistory.objects.get(id=event_id)
			created = False

		except TerritoryWarHistory.DoesNotExist:

			o = TerritoryWarHistory(id=event_id)

		o.guild = guild

		if 'type' in event:
			if event['type'] != 'TERRITORY_WAR_CONFLICT_ACTIVITY':
				#raise Exception('Invalid event type: %s' % event['type'])
				print('Invalid event type: %s' % event['type'])
				print(event)
				return None, False

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
					o.event = TerritoryWar.parse(activity['eventId'])

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
						o.activity = TerritoryWarHistory.ACTIVITY_TYPES[activity_type][0]

			if 'squad' in data and 'squad' in data['squad']:
				o.squad = TerritoryWarSquad.parse(event_id, o.activity, data['squad'])

		o.save()
		return o, created

	class Meta:
		ordering = ('timestamp',)
		unique_together = (('eid', 'event'),)

class TerritoryWarStat(models.Model):

	categories = (
		('stars',             'Total Banners'),
		('set_defense_stars', 'Banners from Setting Defense'),
		('attack_stars',      'Banners from Successful Attacks'),
		('disobey',           'Rogue Actions')
	)

	event = models.ForeignKey(TerritoryWar, on_delete=models.CASCADE)
	guild = models.ForeignKey(Guild, on_delete=models.CASCADE)
	player_id = models.CharField(max_length=22)
	player_name = models.CharField(max_length=64)
	stars = models.IntegerField(default=0)
	set_defense_stars = models.IntegerField(default=0)
	attack_stars = models.IntegerField(default=0)
	disobey = models.IntegerField(default=0)

	def get_score(self, category):
		return hasattr(self, category) and getattr(self, category) or 0

	@staticmethod
	def parse(guild, stats):

		players = {}

		event = TerritoryWar.parse(stats['eventId'])

		for stat in stats['stats']:

			for category, values in stat.items():

				for value in values:

					player_id = value['playerId']
					player_name = value['playerName']
					if player_id not in players:
						players[player_id] = {}
						players[player_id]['player_name'] = player_name

					players[player_id][category] = value['playerScore']

		with transaction.atomic():
			for player_id, defaults in players.items():
				o, created = TerritoryWarStat.objects.update_or_create(event=event, guild=guild, player_id=player_id, defaults=defaults)
				print('TW Stats object %s' % (created and 'created' or 'updated'))

	class Meta:
		ordering = [ '-stars', 'player_name' ]
