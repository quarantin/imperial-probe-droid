from django.db import models, transaction

from swgoh.models import Guild

import pytz
from datetime import datetime

class TerritoryBattle(models.Model):

	TB_TYPE_CHOICES = [
		('TB_EVENT_HOTH_REBEL',          'Hoth - Rebel'),
		('TB_EVENT_HOTH_EMPIRE',         'Hoth - Empire'),
		('TB_EVENT_GEONOSIS_REPUBLIC',   'Genonosis - Republic'),
		('TB_EVENT_GEONOSIS_SEPARATIST', 'Genonosis - Separatist'),
	]

	event_id = models.CharField(max_length=64)
	tb_type = models.CharField(max_length=16, choices=TB_TYPE_CHOICES)
	timestamp = models.DateTimeField()

	def __str__(self):
		return '%s - %s' % (self.get_name(), self.get_date())

	def get_name(self):

		for key, value in TerritoryBattle.TB_TYPE_CHOICES:
			if key == self.tb_type:
				return value

		return 'Unknown'

	def get_date(self, dateformat='%Y-%m-%d'):
		ts = int(self.event_id.split(':')[1][1:-3])
		dt = datetime.fromtimestamp(ts, tz=pytz.utc)
		return dt.strftime(dateformat)

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
	ACTIVITY_RECON       = (5, 'Recon')
	ACTIVITY_RECON_FULL  = (6, 'Recon (Full)')

	ACTIVITY_TYPES = {
		'TERRITORY_CHANNEL_ACTIVITY_CONFLICT_DEPLOY': ACTIVITY_DEPLOY,
		'TERRITORY_CHANNEL_ACTIVITY_COVERT_COMPLETE': ACTIVITY_SPECIAL,
		'TERRITORY_CHANNEL_ACTIVITY_RECON_CONTRIBUTION': ACTIVITY_RECON,
		'TERRITORY_CHANNEL_ACTIVITY_RECON_CONTRIBUTION_ALL_COMPLETE': ACTIVITY_RECON_FULL,
		'TERRITORY_CHANNEL_ACTIVITY_STARS_GAINED': ACTIVITY_STAR,
		'TERRITORY_CHANNEL_ACTIVITY_STRIKE_LINKED_CONFLICT_CONTRIBUTION': ACTIVITY_COMBAT,
		'TERRITORY_CHANNEL_ACTIVITY_STRIKE_LINKED_CONFLICT_CONTRIBUTION_ALL_COMPLETE': ACTIVITY_COMBAT_FULL,
	}

	# TODO TW:
	# TERRITORY_CHANNEL_ACTIVITY_RECON_CONTRIBUTION
	# TERRITORY_CHANNEL_ACTIVITY_RECON_CONTRIBUTION_ALL_COMPLETE
	ACTIVITY_CHOICES = [
		ACTIVITY_DEPLOY,
		ACTIVITY_SPECIAL,
		ACTIVITY_STAR,
		ACTIVITY_COMBAT,
		ACTIVITY_COMBAT_FULL,
		ACTIVITY_RECON,
		ACTIVITY_RECON_FULL,
	]

	TERRITORIES = {

		'TB_EVENT_GEONOSIS_REPUBLIC': {
			1: {
				1: 'Top 1',
				2: 'Middle 1',
				3: 'Bottom 1',
			},
			2: {
				1: 'Top 2',
				2: 'Middle 2',
				3: 'Bottom 2',
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
		},
		'TB_EVENT_GEONOSIS_SEPARATIST': {
			1: {
				1: 'Top 1',
				3: 'Bottom 1',
			},
			2: {
				1: 'Top 2',
				2: 'Middle 2',
				3: 'Bottom 2',
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
		},
	}

	@staticmethod
	def get_activity_by_num(num_activity):
		num_activity = int(num_activity)
		for num, activity in TerritoryBattleHistory.ACTIVITY_CHOICES:
			if num == num_activity:
				return activity

		return 'Unknown'

	id = models.CharField(max_length=64, primary_key=True)
	guild = models.ForeignKey(Guild, on_delete=models.CASCADE, null=True)
	event = models.ForeignKey(TerritoryBattle, on_delete=models.CASCADE)
	timestamp = models.DateTimeField()
	activity = models.IntegerField(choices=ACTIVITY_CHOICES)
	player_id = models.CharField(max_length=22)
	player_name = models.CharField(max_length=64)
	phase = models.IntegerField()
	territory = models.IntegerField()
	score = models.IntegerField(null=True)
	total = models.IntegerField(null=True)

	def get_territory(self):
		tb_type = self.event.tb_type
		return TerritoryBattleHistory.TERRITORIES[tb_type][self.phase][self.territory]

	@staticmethod
	def get_phase_list(tb_type):

		phase_list = {}
		for phase in list(TerritoryBattleHistory.TERRITORIES[tb_type]):
			phase_list[phase] = 'Phase %d' % phase

		return phase_list

	@staticmethod
	def get_territory_list(tb_type):

		territory_list = {}
		for phase, territories in TerritoryBattleHistory.TERRITORIES[tb_type].items():
			for territory, name in territories.items():
				key = '%d-%d' % (phase, territory)
				territory_list[key] = 'Phase %d - %s' % (phase, name)

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
	def get_json_events(events, reverse=False):

		accu = {}
		for event in events:
			score = event.score
			activity = event.activity
			if activity in [ TerritoryBattleHistory.ACTIVITY_RECON[1], TerritoryBattleHistory.ACTIVITY_RECON_FULL[1] ]:
				continue

			player_name = event.player_name
			if player_name not in accu:
				accu[player_name] = 0
			if score and score >= 0:
				accu[player_name] += score

		result = []
		for label, value in sorted(accu.items(), key=lambda x: x[1], reverse=reverse):
			result.append({
				'label': label,
				'value': value,
			})

		return result

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
				#print('Invalid event type: %s' % event['type'])
				return None, False

		o.timestamp = event['timestamp']

		o.guild = guild

		o.player_id = event['playerId']

		o.player_name = event['playerName']

		o.event = TerritoryBattle.parse(event['eventId'])

		o.phase = event['phase']
		o.territory = event['territory']

		o.score = event['score']
		o.total = event['total']

		o.activity = event['eventType']

		o.save()
		return o, created

	class Meta:
		ordering = ('timestamp',)

class TerritoryBattleStat(models.Model):

	categories = (
		('summary',                'Territory Points Contributed'),
		('unit_donated',           'Platoon Mission Units Assigned'),
		('strike_encounter',       'Combat Mission Waves Completed'),
		('disobey',                'Rogue Actions'),
		('score_round_1',          'Phase 1 - Territory Points'),
		('power_round_1',          'Phase 1 - GP Deployed'),
		('strike_attempt_round_1', 'Phase 1 - Combat Missions'),
		('covert_attempt_round_1', 'Phase 1 - Special Missions'),
		('score_round_2',          'Phase 2 - Territory Points'),
		('power_round_2',          'Phase 2 - GP Deployed'),
		('strike_attempt_round_2', 'Phase 2 - Combat Missions'),
		('covert_attempt_round_2', 'Phase 2 - Special Missions'),
		('score_round_3',          'Phase 3 - Territory Points'),
		('power_round_3',          'Phase 3 - GP Deployed'),
		('strike_attempt_round_3', 'Phase 3 - Combat Missions'),
		('covert_attempt_round_3', 'Phase 3 - Special Missions'),
		('score_round_4',          'Phase 4 - Territory Points'),
		('power_round_4',          'Phase 4 - GP Deployed'),
		('strike_attempt_round_4', 'Phase 4 - Combat Missions'),
		('covert_attempt_round_4', 'Phase 4 - Special Missions'),
	)

	event = models.ForeignKey(TerritoryBattle, on_delete=models.CASCADE)
	guild = models.ForeignKey(Guild, on_delete=models.CASCADE)
	player_id = models.CharField(max_length=22)
	player_name = models.CharField(max_length=64)
	summary = models.IntegerField(default=0)
	unit_donated = models.IntegerField(default=0)
	strike_encounter = models.IntegerField(default=0)
	disobey = models.IntegerField(default=0)
	score_round_1 = models.IntegerField(default=0)
	power_round_1 = models.IntegerField(default=0)
	strike_attempt_round_1 = models.IntegerField(default=0)
	covert_attempt_round_1 = models.IntegerField(default=0)
	score_round_2 = models.IntegerField(default=0)
	power_round_2 = models.IntegerField(default=0)
	strike_attempt_round_2 = models.IntegerField(default=0)
	covert_attempt_round_2 = models.IntegerField(default=0)
	score_round_3 = models.IntegerField(default=0)
	power_round_3 = models.IntegerField(default=0)
	strike_attempt_round_3 = models.IntegerField(default=0)
	covert_attempt_round_3 = models.IntegerField(default=0)
	score_round_4 = models.IntegerField(default=0)
	power_round_4 = models.IntegerField(default=0)
	strike_attempt_round_4 = models.IntegerField(default=0)
	covert_attempt_round_4 = models.IntegerField(default=0)

	def get_score(self, category):
		return hasattr(self, category) and getattr(self, category) or 0

	@staticmethod
	def parse(guild, stats):

		players = {}

		event = TerritoryBattle.parse(stats['eventId'])

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
			for player_id, defaults, in players.items():
				o, created = TerritoryBattleStat.objects.update_or_create(event=event, guild=guild, player_id=player_id, defaults=defaults)
				print('TB Stats object %s' % (created and 'created' or 'updated'))

	class Meta:
		ordering = [ '-summary', 'player_name' ]
