from django.db import models

from swgoh.models import Guild

import pytz
from datetime import datetime

class TerritoryBattle(models.Model):

	TB_TYPE_CHOICES = [
		('TB_EVENT_HOTH_REBEL',          'Hoth Rebel - Light Side'),
		('TB_EVENT_HOTH_EMPIRE',         'Hoth Empire - Dark Side'),
		('TB_EVENT_GEONOSIS_REPUBLIC',   'Genonosis - Republic (Light Side)'),
		('TB_EVENT_GEONOSIS_SEPARATIST', 'Genonosis - Separatist (Dark Side)'),
	]

	event_id = models.CharField(max_length=64)
	tb_type = models.CharField(max_length=16, choices=TB_TYPE_CHOICES)
	timestamp = models.DateTimeField()

	def __str__(self):
		return str(self.event_id)

	def get_name(self):

		for key, value in TerritoryBattle.TB_TYPE_CHOICES:
			if key == self.tb_type:
				return value

		return 'Unknown'

	def get_date(self, dateformat='%Y-%m-%d'):
		ts = int(self.event_id.split(':')[1][1:-3])
		dt = datetime.fromtimestamp(ts)
		return pytz.utc.convert(dt).strftime(dateformat)

	@staticmethod
	def parse(event_id):
		tb_type = event_id.split(':')[0]
		ts = int(event_id.split(':')[1][1:-3])
		timestamp = pytz.utc.localize(datetime.fromtimestamp(ts))
		event, created = TerritoryBattle.objects.get_or_create(event_id=event_id, tb_type=tb_type, timestamp=timestamp)

		return event

	class Meta:
		ordering = ('-timestamp',)

class TerritoryBattleHistory(models.Model):

	ACTIVITY_DEPLOY      = (0, 'Deployment')
	ACTIVITY_SPECIAL     = (1, 'Special Mission')
	ACTIVITY_STAR        = (2, 'Star Obtained')
	ACTIVITY_COMBAT      = (3, 'Combat Mission')
	ACTIVITY_COMBAT_FULL = (4, 'Combat Mission (Full)')
	ACTIVITY_RECON       = (5, 'Recon?')

	ACTIVITY_TYPES = {
		'TERRITORY_CHANNEL_ACTIVITY_CONFLICT_DEPLOY': ACTIVITY_DEPLOY,
		'TERRITORY_CHANNEL_ACTIVITY_COVERT_COMPLETE': ACTIVITY_SPECIAL,
		'TERRITORY_CHANNEL_ACTIVITY_RECON_CONTRIBUTION': ACTIVITY_RECON,
		'TERRITORY_CHANNEL_ACTIVITY_STARS_GAINED': ACTIVITY_STAR,
		'TERRITORY_CHANNEL_ACTIVITY_STRIKE_LINKED_CONFLICT_CONTRIBUTION': ACTIVITY_COMBAT,
		'TERRITORY_CHANNEL_ACTIVITY_STRIKE_LINKED_CONFLICT_CONTRIBUTION_ALL_COMPLETE': ACTIVITY_COMBAT_FULL,
	}

	# TODO TW:
	# TERRITORY_CHANNEL_ACTIVITY_RECON_CONTRIBUTION
	# TERRITORY_CHANNEL_ACTIVITY_RECON_CONTRIBUTION_ALL_COMPLETE
	EVENT_TYPE_CHOICES = [
		ACTIVITY_DEPLOY,
		ACTIVITY_SPECIAL,
		ACTIVITY_STAR,
		ACTIVITY_COMBAT,
		ACTIVITY_COMBAT_FULL,
	]

	@staticmethod
	def get_activity_by_num(num_activity):
		for num, activity in TerritoryBattleHistory.EVENT_TYPE_CHOICES:
			if num == num_activity:
				return activity

		return 'Unknown'

	id = models.CharField(max_length=64, primary_key=True)
	guild = models.ForeignKey(Guild, on_delete=models.CASCADE, null=True)
	tb = models.ForeignKey(TerritoryBattle, on_delete=models.CASCADE)
	timestamp = models.DateTimeField()
	event_type = models.IntegerField(choices=EVENT_TYPE_CHOICES)
	player_id = models.CharField(max_length=22)
	player_name = models.CharField(max_length=64)
	phase = models.IntegerField()
	territory = models.IntegerField()
	score = models.IntegerField(null=True)
	total = models.IntegerField(null=True)

	@property
	def get_territory(self):
		return None

	@staticmethod
	def get_territory_list():

		territory_list = {}
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
			o = TerritoryBattleHistory.objects.get(id=event_id)
			created = False

		except TerritoryBattleHistory.DoesNotExist:

			o = TerritoryBattleHistory(id=event_id)

		if 'type' in event:
			if event['type'] != 'TERRITORY_CONFLICT_ACTIVITY':
				print('Invalid event type: %s' % event['type'])
				return None, False

		o.timestamp = event['timestamp']

		o.player_id = event['playerId']

		o.player_name = event['playerName']

		o.tb = TerritoryBattle.parse(event['eventId'])

		o.phase = event['phase']
		o.territory = event['territory']

		o.score = event['score']
		o.total = event['total']

		o.event_type = event['eventType']

		o.save()
		return o, created

	class Meta:
		ordering = ('timestamp',)
