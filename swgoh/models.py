from django.db import models
from django.db import transaction

import os, requests
from datetime import datetime

from .utils import download, expired

CACHE = {}

ALIGNMENTS = (
	('ls', 'Light Side'),
	('ds', 'Dark Side'),
)

COMBAT_TYPES = (
	(1, 'Character'),
	(2, 'Ship'),
)

MODSETS = (
	(1, 'Health'),
	(2, 'Offense'),
	(3, 'Defense'),
	(4, 'Speed'),
	(5, 'Critical Chance'),
	(6, 'Critical Damage'),
	(7, 'Potency'),
	(8, 'Tenacity'),
)

ROLES = (
	('attacker',     'Attacker'),
	('capital-ship', 'Capital Ship'),
	('healer',       'Healer'),
	('leader',       'Leader'),
	('support',      'Support'),
	('tank',         'Tank'),
)

class Player(models.Model):

	LANGS = (
		('chs_cn', 'cs', '', 'Chinese (Simplified)'),
		('cht_cn', 'ct', '', 'Chinese (Traditional)'),
		('eng_us', 'us', '', 'English'),
		('fre_fr', 'fr', '', 'French'),
		('ger_de', 'de', '', 'German'),
		('ind_id', 'id', '', 'Indy'),
		('ita_it', 'it', '', 'Italian'),
		('jpn_jp', 'jp', '', 'Japanese'),
		('kor_kr', 'kr', '', 'Korean'),
		('por_br', 'pt', '', 'Portugese (Brazil)'),
		('rus_ru', 'ru', '', 'Russian'),
		('spa_xm', 'sp', '', 'Spanish (Latino)'),
		('tha_th', 'th', '', 'Thai'),
		('tur_tr', 'tr', '', 'Turkish'),
	)

	BOT_LANGUAGES = ( (short_code, name) for code, short_code, flag, name in LANGS )

	LANGUAGES = ( (code, name) for code, short_code, flag, name in LANGS )

	def get_language_info(lang):
		for code, short_code, flag, name in Player.LANGS:
			if code == lang or short_code == lang or flag == lang or name == lang:
				return code, short_code, flag, name

		return None

	discord_id           = models.IntegerField(unique=True)
	discord_name         = models.CharField(max_length=128, default='', blank=True, null=True)
	discord_nick         = models.CharField(max_length=128, default='', blank=True, null=True)
	discord_display_name = models.CharField(max_length=128, default='', blank=True, null=True)
	game_nick            = models.CharField(max_length=128, default='', blank=True, null=True)
	ally_code            = models.IntegerField(blank=True, null=True)
	language             = models.CharField(max_length=6, default='eng_us', choices=LANGUAGES)

	def format_ally_code(ally_code):
		ally_code = str(ally_code)
		return '%s-%s-%s' % (ally_code[0:3], ally_code[3:6], ally_code[6:9])

	def get_ally_code(self):
		return Player.format_ally_code(self.ally_code)

	def get_player_by_nick(nick):

		from django.db.models import Q
		match_name = Q(discord_name=nick)
		match_nick = Q(discord_nick=nick)
		match_display_name = Q(discord_display_name=nick)
		match_game_nick = Q(game_nick=nick)

		try:
			return Player.objects.get(match_name|match_nick|match_display_name|match_game_nick)

		except Player.DoesNotExist:
			return None

	def get_ally_code_by_nick(nick):
		p = Player.get_player_by_nick(nick)
		return p and p.ally_code or None

	def __str__(self):
		if self.discord_display_name:
			return self.discord_display_name

		if self.discord_nick:
			return self.discord_nick

		if self.discord_name:
			return self.discord_name

		return self.discord_id

class Gear(models.Model):

	MARKS = (
		("Mk I",    "Mk I"),
		("Mk II",   "Mk II"),
		("Mk III",  "Mk III"),
		("Mk IV",   "Mk IV"),
		("Mk V",    "Mk V"),
		("Mk VI",   "Mk VI"),
		("Mk VII",  "Mk VII"),
		("Mk VIII", "Mk VIII"),
		("Mk IX",   "Mk IX"),
		("Mk X",    "Mk X"),
		("Mk XI",   "Mk XI"),
		("Mk XII",  "Mk XII"),
	)

	TIERS = (
		(1,  1),
		(2,  2),
		(3,  3),
		(4,  4),
		(5,  5),
		(6,  6),
		(7,  7),
		(8,  8),
		(9,  9),
		(10, 10),
		(11, 11),
		(12, 12),
	)

	base_id = models.CharField(max_length=128, unique=True)
	name = models.CharField(max_length=128)
	tier = models.IntegerField(choices=TIERS)
	required_level = models.IntegerField()
	mark = models.CharField(max_length=16, choices=MARKS)
	cost = models.IntegerField()
	url = models.CharField(max_length=255)
	image = models.CharField(max_length=255)

	def get_all_gear():
		url = 'https://swgoh.gg/api/gear/'
		gear_list, from_cache = download(url)
		cache_key = 'Gear.get_all_gear'
		parsed = cache_key in CACHE and not expired(CACHE[cache_key])
		if not from_cache or not parsed:
			with transaction.atomic():
				for gear in gear_list:

					gear = dict(gear)

					recipes     = gear.pop('recipes')
					stats       = gear.pop('stats')
					ingredients = gear.pop('ingredients')

					gear['url']   = gear['url'].replace('//swgoh.gg/db/gear/', '')
					gear['image'] = os.path.basename(gear['image'])

					Gear.objects.update_or_create(**gear)

				CACHE[cache_key] = datetime.now()

		return list(Gear.objects.all())

	def get_all_gear_by_id():
		result = {}
		all_gear = Gear.get_all_gear()
		for gear in all_gear:
			result[gear.base_id] = gear
		return result

	def get_image(self):
		return 'https://swgoh.gg/%s' % self.image

	def get_url(self):
		return 'https://swgoh.gg/%s' % self.url

class BaseUnit(models.Model):

	SHIP_SLOTS = (
		('', None),
		(0, '0'),
		(1, '1'),
		(2, '2'),
	)

	base_id = models.CharField(max_length=128)
	name = models.CharField(max_length=128)
	alignment = models.CharField(max_length=32, choices=ALIGNMENTS)
	role = models.CharField(max_length=32, choices=ROLES)
	power = models.IntegerField()
	combat_type = models.IntegerField(choices=COMBAT_TYPES)
	description = models.CharField(max_length=255)
	url = models.CharField(max_length=255)
	image = models.CharField(max_length=255)
	activate_shard_count = models.IntegerField()
	ship = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
	ship_slot = models.CharField(max_length=8, choices=SHIP_SLOTS, null=True)
	capital_ship = models.BooleanField(default=False)

	def __str__(self):
		return self.name

	def get_units_by_faction(factions):

		selected_units = []

		try:
			facs = BaseUnitFaction.objects.filter(faction__in=factions)

			base_ids = []
			for faction in facs:
				print(faction.faction)
				if faction.unit.base_id not in base_ids:
					base_ids.append(faction.unit.base_id)

			units = BaseUnit.objects.filter(base_id__in=base_ids)
			for unit in units:
				if unit not in selected_units:
					selected_units.append(unit)

		except BaseUnitFaction.DoesNotExist:
			pass

		return sorted(selected_units, key=lambda x: x.name)

	def get_all_units():
		return list(BaseUnit.objects.filter(combat_type=1).order_by('name'))

	def get_all_ships():
		return list(BaseUnit.objects.filter(combat_type=2).order_by('name'))

	def get_all_units_by_id():
		result = {}
		all_units = BaseUnit.get_all_units()
		for unit in all_units:
			result[unit.base_id] = unit
		return result

	def get_image(self):
		return 'https://swgoh.gg/%s' % self.image

	def get_url(self):
		return 'https://swgoh.gg/%s' % self.url

class BaseUnitFaction(models.Model):

	FACTIONS = [
		('profession_bountyhunter',     'Bounty Hunters'),
		('profession_clonetrooper',     'Clone Trooper'),
		('profession_jedi',             'Jedi'),
		('profession_scoundrel',        'Scoundrel'),
		('profession_sith',             'Sith'),
		('profession_smuggler',         'Smuggler'),
		('affiliation_empire',          'Empire'),
		('affiliation_firstorder',      'First Order'),
		('affiliation_imperialtrooper', 'Imperial Trooper'),
		('affiliation_nightsisters',    'Nightsister'),
		('affiliation_oldrepublic',     'Old Republic'),
		('affiliation_phoenix',         'Phoenix'),
		('affiliation_rebels',          'Rebel'),
		('affiliation_republic',        'Galactic Republic'),
		('affiliation_resistance',      'Resistance'),
		('affiliation_rogue_one',       'Rogue One'),
		('affiliation_separatist',      'Separatist'),
		('affiliation_sithempire',      'Sith Empire'),
		('species_droid',               'Droid'),
		('species_ewok',                'Ewok'),
		('species_geonosian',           'Geonosian'),
		('species_human',               'Human'),
		('species_jawa',                'Jawa'),
		('species_tusken',              'Tusken'),
		('species_wookiee',             'Wookie'),
	]

	FACTION_NICKS = {
		'bh':            'bountyhunter',
		'bountyhunters': 'bountyhunter',
		'droids':        'droid',
		'ewoks':         'ewok',
		'fo':            'firstorder',
		'galactic':      'republic',
		'geos':          'geonosian',
		'geonosians':    'geonosian',
		'humans':        'human',
		'jawas':         'jawa',
		'jedis':         'jedi',
		'ns':            'nightsisters',
		'or':            'oldrepublic',
		'r1':            'rogue_one',
		'rebells':       'rebels',
		'rebelles':      'rebels',
		'separatists':   'separatist',
		'siths':         'sith',
		'tuskens':       'tusken',
		'wookies':       'wookiee',
		'wookiees':      'wookiee',
	}

	unit = models.ForeignKey(BaseUnit, on_delete=models.CASCADE)
	faction = models.CharField(max_length=32, choices=FACTIONS)

	def is_supported_faction(faction):
		for fac_id, fac_name in BaseUnitFaction.FACTIONS:
			if fac_id == faction or fac_name.lower() == faction.lower():
				return fac_id
		return False

class BaseUnitAbilityClass(models.Model):

	ABILITIES = (
		('Ability Block',        'Ability Block'),
		('Advantage',            'Advantage'),
		('Anti-Droid',           'Anti-Droid'),
		('AoE',                  'AoE'),
		('Assist',               'Assist'),
		('Bonus Attack',         'Bonus Attack'),
		('Buff Immunity',        'Buff Immunity'),
		('Counter',              'Counter'),
		('Daze',                 'Daze'),
		('Defense Down',         'Defense Down'),
		('Defense Up',           'Defense Up'),
		('Dispel',               'Dispel'),
		('Dispel - All Enemies', 'Dispel - All Enemies'),
		('DoT',                  'DoT'),
		('Evasion Down',         'Evasion Down'),
		('Evasion Up',           'Evasion Up'),
		('Expose',               'Expose'),
		('Foresight',            'Foresight'),
		('Gain Turn Meter',      'Gain Turn Meter'),
		('Heal',                 'Heal'),
		('Healing Immunity',     'Healing Immunity'),
		('Leader: Assist',       'Leader: Assist'),
		('Leader: +Critical',    'Leader: +Critical'),
		('Leader: +Defense',     'Leader: +Defense'),
		('Leader: +Evasion',     'Leader: +Evasion'),
		('Leader: Foresight',    'Leader: Foresight'),
		('Leader: Healing',      'Leader: Healing'),
		('Leader: +Max Health',  'Leader: +Max Health'),
		('Leader: +Speed',       'Leader: +Speed'),
		('Leader: +Tenacity',    'Leader: +Tenacity'),
		('Offense Down',         'Offense Down'),
		('Offense Up',           'Offense Up'),
		('Reduce Cooldowns',     'Reduce Cooldowns'),
		('Remove Turn Meter',    'Remove Turn Meter'),
		('Reset Cooldown',       'Reset Cooldown'),
		('Revive',               'Revive'),
		('Speed Down',           'Speed Down'),
		('Stealth',              'Stealth'),
		('Stun',                 'Stun'),
		('Target Lock',          'Target Lock'),
		('Taunt',                'Taunt'),
		('Tenacity Down',        'Tenacity Down'),
		('Tenacity Up',          'Tenacity Up'),
		('Thermal Detonator',    'Thermal Detonator'),
	)
	
	unit = models.ForeignKey(BaseUnit, on_delete=models.CASCADE)
	ability = models.CharField(max_length=32, choices=ABILITIES)

class BaseUnitGear(models.Model):

	unit = models.ForeignKey(BaseUnit, on_delete=models.CASCADE)
	gear = models.ForeignKey(Gear, on_delete=models.CASCADE)
	tier = models.IntegerField()
	slot = models.IntegerField()

	def __str__(self):
		return '%s / %d / %d / %s' % (self.unit.name, self.tier, self.slot, self.gear.name)

	def populate_gear_level(unit):
		all_gear = Gear.get_all_gear_by_id()
		all_units = BaseUnit.get_all_units_by_id()

		unit_id = unit['base_id']
		base_unit = all_units[unit_id]
		for level in unit['gear_levels']:
			tier = level['tier']
			for slot, gear_id in enumerate(level['gear']):
				gear = all_gear[gear_id]
				BaseUnitGear.objects.update_or_create(unit=base_unit, gear=gear, tier=tier, slot=slot)

	def get_all_unit_gear_levels():
		url = 'https://swgoh.gg/api/characters/'
		units, from_cache = download(url)
		cache_key = 'BaseUnitGear.get_all_unit_gear_levels'
		parsed = cache_key in CACHE and not expired(CACHE[cache_key])
		if not from_cache or not parsed:
			with transaction.atomic():
				for unit in units:
					BaseUnitGear.populate_gear_level(unit)

				CACHE[cache_key] = datetime.now()

		return BaseUnitGear.objects.all()

	def get_unit_gear_levels(base_id):
		url = 'https://swgoh.gg/api/characters/'
		units, from_cache = download(url)
		cache_key = 'BaseUnitGear.get_all_unit_gear_levels'
		parsed = cache_key in CACHE and not expired(CACHE[cache_key])
		if not from_cache or not parsed:
			cache_key = 'BaseUnitGear.get_unit_gear_levels.%s' % base_id
			parsed = cache_key in CACHE and not expired(CACHE[cache_key])
			if not parsed:
				with transaction.atomic():
					for unit in units:
						if unit['base_id'] == base_id:
							BaseUnitGear.populate_gear_level(unit)
							CACHE[cache_key] = datetime.now()
							break

		return BaseUnitGear.objects.filter(unit__base_id=base_id)

class BaseUnitSkill(models.Model):
	skill_id = models.CharField(max_length=30)
	is_zeta = models.BooleanField(default=False)
	unit = models.ForeignKey(BaseUnit, on_delete=models.CASCADE)

class PlayerCharacter(models.Model):
	player = models.ForeignKey(Player, on_delete=models.CASCADE)
	character = models.ForeignKey(BaseUnit, on_delete=models.CASCADE)

class Mod(models.Model):

	SLOTS = (
		(1, 'Square'),
		(2, 'Arrow'),
		(3, 'Diamond'),
		(4, 'Triangle'),
		(5, 'Circle'),
		(6, 'Cross'),
	)

	PRIMARIES = (
		('ac', 'Accuracy'),
		('ca', 'Critical Avoidance'),
		('cc', 'Critical Chance'),
		('cd', 'Critical Damage'),
		('de', 'Defense'),
		('he', 'Health'),
		('of', 'Offense'),
		('po', 'Potency'),
		('pr', 'Protection'),
		('sp', 'Speed'),
		('te', 'Tenacity'),
	)

	SECONDARIES = (
		('cc', 'Critical Chance'),
		('sp', 'speed'),
	)

	character = models.ForeignKey(PlayerCharacter, on_delete=models.CASCADE)

	slot = models.CharField(max_length=16, choices=SLOTS)
	modset = models.CharField(max_length=16, choices=MODSETS)
	primary_stat = models.CharField(max_length=16, choices=PRIMARIES)
	secondary_stat_1 = models.CharField(max_length=16, choices=SECONDARIES)
	secondary_stat_2 = models.CharField(max_length=16, choices=SECONDARIES)
	secondary_stat_3 = models.CharField(max_length=16, choices=SECONDARIES)
	secondary_stat_4 = models.CharField(max_length=16, choices=SECONDARIES)
	secondary_stat_value_1 = models.CharField(max_length=8)
	secondary_stat_value_2 = models.CharField(max_length=8)
	secondary_stat_value_3 = models.CharField(max_length=8)
	secondary_stat_value_4 = models.CharField(max_length=8)
	secondary_stat_rolls_1 = models.IntegerField(default=0)
	secondary_stat_rolls_2 = models.IntegerField(default=0)
	secondary_stat_rolls_3 = models.IntegerField(default=0)
	secondary_stat_rolls_4 = models.IntegerField(default=0)

class ModRecommendation(models.Model):
	SOURCES = (
		('cg', 'Capital Games'),
		('cr', 'Crouching Rancor'),
		('sw', 'Swgoh.gg'),
	)

	SQUARE_PRIMARIES = (
		('offense%', 'Offense %'),
	)

	ARROW_PRIMARIES = (
		('accuracy%', 'Accuracy %'),
		('critical-avoidance%', 'Critical Avoidance %'),
		('defense%', 'Defense %'),
		('health%', 'Health %'),
		('offense%', 'Offense %'),
		('protection%', 'Protection %'),
		('speed', 'Speed'),
	)

	DIAMOND_PRIMARIES = (
		('defense%', 'Defense %'),
	)

	TRIANGLE_PRIMARIES = (
		('critical-chance%', 'Critical Chance %'),
		('critical-damage%', 'Critical Damage %'),
		('defense%', 'Defense %'),
		('health%', 'Health %'),
		('offense%', 'Offense %'),
		('protection%', 'Protection %'),

	)

	CIRCLE_PRIMARIES = (
		('health%', 'Health %'),
		('protection%', 'Protection %'),
	)

	CROSS_PRIMARIES = (
		('defense%', 'Defense %'),
		('health%', 'Health %'),
		('offense%', 'Offense %'),
		('potency%', 'Potency %'),
		('protection%', 'Protection %'),
		('tenacity%', 'Tenacity %'),
	)

	character = models.ForeignKey(BaseUnit, on_delete=models.CASCADE)
	source = models.CharField(max_length=32, choices=SOURCES)
	modset1 = models.CharField(max_length=32, choices=MODSETS)
	modset2 = models.CharField(max_length=32, choices=MODSETS)
	modset3 = models.CharField(max_length=32, choices=MODSETS)
	square = models.CharField(max_length=32, choices=SQUARE_PRIMARIES)
	arrow = models.CharField(max_length=32, choices=ARROW_PRIMARIES)
	diamond = models.CharField(max_length=32, choices=DIAMOND_PRIMARIES)
	triangle = models.CharField(max_length=32, choices=TRIANGLE_PRIMARIES)
	circle = models.CharField(max_length=32, choices=CIRCLE_PRIMARIES)
	cross = models.CharField(max_length=32, choices=CROSS_PRIMARIES)
	info = models.CharField(max_length=255, default='', blank=True)

class Translation(models.Model):

	string_id = models.CharField(max_length=64)
	context = models.CharField(max_length=16)
	translation = models.CharField(max_length=64)
	language = models.CharField(max_length=6, choices=Player.LANGUAGES)

	class Meta:
		unique_together = [ 'string_id', 'context', 'language' ]

class Shard(models.Model):

	SHARD_TYPES = (
		('char', 'Character Arena'),
		('ship', 'Ship Arena'),
	)

	SHARD_TYPES_DICT = { x: y for x, y in SHARD_TYPES }

	type = models.CharField(max_length=8, choices=SHARD_TYPES)
	player = models.ForeignKey(Player, on_delete=models.CASCADE)

	class Meta:
		unique_together = [ 'player', 'type' ]

class ShardMember(models.Model):

	shard = models.ForeignKey(Shard, on_delete=models.CASCADE)
	ally_code = models.CharField(max_length=12)
