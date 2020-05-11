from django.db import models

import pytz
from datetime import datetime

class TerritoryBattle(models.Model):

	TB_TYPE_CHOICES = [
		('TB_EVENT_HOTH_REBEL',          'Hoth Rebel - Light Side'),
		('TB_EVENT_HOTH_EMPIRE',         'Hoth Empire - Dark Side'),
		('TB_EVENT_GEONOSIS_REPUBLIC',   'Genonosis - Republic (Light Side)'),
		('TB_EVENT_GEONOSIS_SEPARATIST', 'Genonosis - Separatist (Dark Side)'),
	]

	tb_id = models.CharField(max_length=64)
	tb_type = models.CharField(max_length=16, choices=TB_TYPE_CHOICES)

	def __str__(self):
		return self.tb_type + ':O' + self.tb_id

	def get_name(self):

		for key, value in TerritoryBattle.TB_TYPE_CHOICES:
			if key == self.tb_type:
				return value

		return 'Unknown'

	def get_date(self, dateformat='%Y-%m-%d'):
		return pytz.utc.convert(datetime.fromtimestamp(int(self.tb_id))).strftime(dateformat)

	@staticmethod
	def parse(event_id):

		tokens = event_id.split(':')

		tb_id = tokens[1][1:]
		tb_type = tokens[0]

		event, created = TerritoryBattle.objects.get_or_create(tb_type=tb_type, tb_id=tb_id)

		return event

class TerritoryBattleHistory(models.Model):

	ACTIVITY_DEPLOY      = (0, 'Deployment')
	ACTIVITY_SPECIAL     = (1, 'Special Mission')
	ACTIVITY_STAR        = (2, 'Star Obtained')
	ACTIVITY_COMBAT      = (3, 'Combat Mission')
	ACTIVITY_COMBAT_FULL = (4, 'Combat Mission (Full)')

	ACTIVITY_TYPES = {
		'TERRITORY_CHANNEL_ACTIVITY_CONFLICT_DEPLOY': ACTIVITY_DEPLOY,
		'TERRITORY_CHANNEL_ACTIVITY_COVERT_COMPLETE': ACTIVITY_SPECIAL,
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
	tb = models.ForeignKey(TerritoryBattle, on_delete=models.CASCADE)
	timestamp = models.DateTimeField()
	event_type = models.IntegerField(choices=EVENT_TYPE_CHOICES)
	player_id = models.CharField(max_length=22)
	player_name = models.CharField(max_length=64)
	phase = models.IntegerField()
	territory = models.IntegerField()
	score = models.IntegerField(null=True)
	total = models.IntegerField(null=True)

	class Meta:
		ordering = ('timestamp',)