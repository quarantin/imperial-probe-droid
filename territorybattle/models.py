from django.db import models

class TerritoryBattleHistory(models.Model):

	id = models.CharField(max_length=64, primary_key=True)
	event_id = models.CharField(max_length=64)
	entry_type = models.CharField(max_length=64)
	timestamp = models.IntegerField()
	player_id = models.CharField(max_length=22)
	player_name = models.CharField(max_length=64)
	phase = models.IntegerField()
	territory = models.IntegerField()
	score = models.IntegerField(null=True)
	total = models.IntegerField(null=True)
