from django.db import models

class GrandArena(models.Model):

	event_id = models.CharField(max_length=64)

	def __str__(self):
		return str(self.event_id)

	def get_name(self):
		return 'Grand Arena'

	def get_date(self, dateformat='%Y-%m-%d'):
		ts = int(self.event_id.split(':')[1][1:-3])
		dt = datetime.fromtimestamp(ts)
		return pytz.utc.convert(dt).strftime(dateformat)

	@staticmethod
	def parse(event_id):
		event, created = GrandArena.objects.get_or_create(event_id=event_id)
		return event

	class Meta:
		ordering = ('event_id',)

class GrandArenaHistory(models.Model):
	id = models.CharField(max_length=64, primary_key=True)
	ga = models.ForeignKey(GrandArena, on_delete=models.CASCADE)
	timestamp = models.DateTimeField()
	player_id = models.CharField(max_length=22)
	player_name = models.CharField(max_length=64)
	opponent_id = models.CharField(max_length=22)
	opponent_name = models.CharField(max_length=64)
	phase = models.IntegerField()
	territory = models.IntegerField()
