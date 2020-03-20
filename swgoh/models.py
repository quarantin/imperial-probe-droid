from django.db import models
from django.db import transaction
from timezone_field import TimeZoneField

import os, pytz, requests
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
		('por_br', 'pt', '', 'Portuguese (Brazil)'),
		('rus_ru', 'ru', '', 'Russian'),
		('spa_xm', 'sp', '', 'Spanish (Latino)'),
		('tha_th', 'th', '', 'Thai'),
		('tur_tr', 'tr', '', 'Turkish'),
	)

	BOT_LANGUAGES = ( (short_code, name) for code, short_code, flag, name in LANGS )

	LANGUAGES = ( (code, name) for code, short_code, flag, name in LANGS )

	def get_language_info(lang):
		llang = lang.lower()
		for code, short_code, flag, name in Player.LANGS:
			if code == llang or short_code == llang or name.split()[0].lower() == llang:
				return code, short_code, flag, name

		return None

	discord_id           = models.IntegerField(unique=True, blank=True, null=True)
	discord_name         = models.CharField(max_length=128, default='', blank=True, null=True)
	discord_nick         = models.CharField(max_length=128, default='', blank=True, null=True)
	discord_display_name = models.CharField(max_length=128, default='', blank=True, null=True)
	game_nick            = models.CharField(max_length=128, default='', blank=True, null=True)
	ally_code            = models.IntegerField(blank=True, null=True)
	language             = models.CharField(max_length=6, default='eng_us', choices=LANGUAGES)
	timezone             = TimeZoneField(blank=True, null=True)
	banned               = models.BooleanField(default=False)

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

	def is_banned(author):

		try:
			player = Player.objects.get(discord_id=author.id)
			return player.banned

		except Player.DoesNotExist:
			pass

		return False

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

	base_id = models.CharField(max_length=128, primary_key=True)
	name = models.CharField(max_length=128)
	tier = models.IntegerField(choices=TIERS)
	required_level = models.IntegerField()
	mark = models.CharField(max_length=16, choices=MARKS)
	cost = models.IntegerField()
	url = models.CharField(max_length=255)
	image = models.CharField(max_length=255)

	def __str__(self):
		return self.name

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

					gear['url']   = gear['url'].replace('//swgoh.gg', '')
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
		return 'https://swgoh.gg%s' % self.image

	def get_url(self):
		return 'https://swgoh.gg%s' % self.url

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
				if faction.unit.base_id not in base_ids:
					base_ids.append(faction.unit.base_id)

			units = BaseUnit.objects.filter(base_id__in=base_ids)
			for unit in units:

				if unit not in selected_units:
					selected_units.append(unit)

		except BaseUnitFaction.DoesNotExist:
			pass

		return sorted(selected_units, key=lambda x: x.name)

	@staticmethod
	def get_alignment(base_id):

		unit = BaseUnit.objects.get(base_id=base_id)
		align = unit.alignment
		if align in [ 'ls', 'Light Side' ]:
			return 'light'

		if align in [ 'ds', 'Dark Side' ]:
			return 'dark'

		return 'neutral'

	def is_ship(base_id):
		try:
			ship = BaseUnit.objects.get(base_id=base_id)
			return ship.combat_type == 2
		except:
			return False

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
		return 'https://swgoh.gg%s' % self.image

	def get_url(self):
		return 'https://swgoh.gg%s' % self.url

class BaseUnitFaction(models.Model):

	FACTIONS = [
		('profession_bountyhunter',     'Bounty Hunters'),
		('profession_clonetrooper',     'Clone Trooper'),
		('profession_jedi',             'Jedi'),
		('profession_scoundrel',        'Scoundrel'),
		('profession_sith',             'Sith'),
		('profession_smuggler',         'Smuggler'),
		('affiliation_501st',           '501st'),
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

# TODO Use me
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
	ability_ref = models.CharField(max_length=30)
	is_zeta = models.BooleanField(default=False)
	unit = models.ForeignKey(BaseUnit, on_delete=models.CASCADE)

	def get_zetas():
		zetas = {}
		skills = list(BaseUnitSkill.objects.filter(is_zeta=True).values('skill_id', 'ability_ref'))
		for skill in skills:
			skill_id = skill['skill_id']
			ability_ref = skill['ability_ref']
			zetas[skill_id] = True
			zetas[ability_ref] = True

		return zetas

# TODO Use me
class PlayerUnit(models.Model):
	player = models.ForeignKey(Player, on_delete=models.CASCADE)
	character = models.ForeignKey(BaseUnit, on_delete=models.CASCADE)

# TODO Use me
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

	character = models.ForeignKey(PlayerUnit, on_delete=models.CASCADE)

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
	set1 = models.CharField(max_length=32, choices=MODSETS)
	set2 = models.CharField(max_length=32, choices=MODSETS)
	set3 = models.CharField(max_length=32, choices=MODSETS)
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
		('ship', 'Fleet Arena'),
	)

	SHARD_TYPES_DICT = { x: y for x, y in SHARD_TYPES }

	channel_id = models.IntegerField(primary_key=True)
	message_id = models.IntegerField(null=True)
	type = models.CharField(max_length=4, choices=SHARD_TYPES)
	hour_interval = models.IntegerField(default=1)
	minute_interval = models.IntegerField(default=45)

class ShardMember(models.Model):

	AFFILIATION_ID_NEUTRAL  = 0
	AFFILIATION_ID_FRIENDLY = 1
	AFFILIATION_ID_ENEMY    = 2

	AFFILIATION_FRIENDLY    = '\U0001f7e2' # Green circle
	AFFILIATION_NEUTRAL     = '\U0001f7e0' # Orange circle
	AFFILIATION_ENEMY       = '\U0001f534' # Red circle

	AFFILIATIONS = (
		(AFFILIATION_ID_NEUTRAL,  AFFILIATION_NEUTRAL),
		(AFFILIATION_ID_FRIENDLY, AFFILIATION_FRIENDLY),
		(AFFILIATION_ID_ENEMY,    AFFILIATION_ENEMY),
	)

	OPTS_AFFILIATIONS = {
		'neutral':  (AFFILIATION_ID_NEUTRAL,  AFFILIATION_NEUTRAL),
		'friend':   (AFFILIATION_ID_FRIENDLY, AFFILIATION_FRIENDLY),
		'friendly': (AFFILIATION_ID_FRIENDLY, AFFILIATION_FRIENDLY),
		'enemy':    (AFFILIATION_ID_ENEMY,    AFFILIATION_ENEMY),
	}

	shard = models.ForeignKey(Shard, on_delete=models.CASCADE)
	ally_code = models.IntegerField()
	affiliation = models.IntegerField(default=0, choices=AFFILIATIONS)
	payout_time = models.TimeField(blank=True, null=True)

	def parse_affiliation(args):

		args_cpy = list(args)

		for arg in args_cpy:

			larg = arg.lower()

			if larg in ShardMember.OPTS_AFFILIATIONS:
				args.remove(arg)
				affil_id, affil_display = ShardMember.OPTS_AFFILIATIONS[larg]
				return (affil_id, affil_display, larg)

		return (None, None, None)

class DiscordServer(models.Model):

	server_id = models.IntegerField(primary_key=True)
	bot_prefix = models.CharField(max_length=32)

class NewsFeed(models.Model):

	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=32, unique=True)
	url = models.CharField(max_length=2048, unique=True)

class NewsEntry(models.Model):

	id = models.AutoField(primary_key=True)
	link = models.CharField(unique=True, max_length=2048)
	published = models.DateTimeField()
	feed = models.ForeignKey(NewsFeed, on_delete=models.CASCADE)

class NewsChannel(models.Model):

	channel_id = models.IntegerField(primary_key=True)
	webhook_id = models.IntegerField(unique=True)
	last_news = models.ForeignKey(NewsEntry, on_delete=models.SET_NULL, null=True)

class ZetaStat(models.Model):

	unit = models.ForeignKey(BaseUnit, on_delete=models.CASCADE)
	skill_id = models.CharField(max_length=32)
	total_zetas = models.IntegerField()
	of_all_zetas = models.FloatField()
	of_all_this_unit = models.FloatField()
	of_g11_this_unit = models.FloatField()

class Gear13Stat(models.Model):

	unit = models.ForeignKey(BaseUnit, on_delete=models.CASCADE)
	g13_count = models.IntegerField()
	total_count = models.IntegerField()
	percentage = models.FloatField()

class RelicStat(models.Model):

	unit = models.ForeignKey(BaseUnit, on_delete=models.CASCADE)
	g13_units = models.IntegerField()
	relic1 = models.IntegerField()
	relic2 = models.IntegerField()
	relic3 = models.IntegerField()
	relic4 = models.IntegerField()
	relic5 = models.IntegerField()
	relic6 = models.IntegerField()
	relic7 = models.IntegerField()
	relic1_percentage = models.FloatField()
	relic2_percentage = models.FloatField()
	relic3_percentage = models.FloatField()
	relic4_percentage = models.FloatField()
	relic5_percentage = models.FloatField()
	relic6_percentage = models.FloatField()
	relic7_percentage = models.FloatField()

class PremiumGuild(models.Model):

	ally_code = models.IntegerField()
	guild_id = models.CharField(max_length=32)
	channel_id = models.IntegerField(null=True, blank=True)
	language = models.CharField(max_length=6, default='eng_us', choices=Player.LANGUAGES)

	def get_guild(guild_id):
		return PremiumGuild.objects.get(guild_id=guild_id)

	def find_guild_for_selector(selector, guilds=None):

		for guild in guilds:
			for member in guild['roster']:
				if str(member['allyCode']) == str(selector):
					return guild

		return None

	def guilds_to_dict(guild_selectors, guilds):

		result = {}
		for selector in guild_selectors:
			guild = PremiumGuild.find_guild_for_selector(selector, guilds)
			if not guild:
				print('Could not find guild for allycode: %s' % selector)
				continue

			result[selector] = guild

		return result

	def get_guild_selectors():

		result = []
		selectors = PremiumGuild.objects.all().values('ally_code')
		for selector in selectors:
			result.append(str(selector['ally_code']))

		return result

	def get_config_value(self, item):

		if item.value_type == 'int':
			return int(item.value)

		if item.value_type == 'bool':
			return item.value == 'True' and True or False

		return str(item.value)

	def get_config(self):

		default_mention = '**Off**'
		default_channel = self.channel_id and '<#%s>' % self.channel_id or None

		config = {}

		config['language'] = self.language
		config['default.channel'] = default_channel

		# Get explicit config from DB
		items = PremiumGuildConfig.objects.filter(guild=self)
		for item in items:

			if item.key.endswith('.channel'):
				config[item.key] = '<#%s>' % item.value

			elif item.value_type == 'int':
				config[item.key] = int(item.value)

			else:
				config[item.key] = self.get_config_value(item)

		# Get default settings if not set
		for key, value, value_type in PremiumGuildConfig.MESSAGE_DEFAULTS:
			if key not in config:
				config[key] = value

		# Get channels, formats, and mentions settings if not set
		for key, fmt in PremiumGuildConfig.MESSAGE_FORMATS.items():

			channel_key = '%s.channel' % key
			if channel_key not in config:
				config[channel_key] = default_channel

			format_key = '%s.format' % key
			if format_key not in config:
				config[format_key] = fmt

			mention_key = '%s.mention' % key
			if mention_key not in config:
				config[mention_key] = default_mention

		return config

	def get_channels(self):

		channels = {}

		default_channel = self.channel_id and '<#%s>' % self.channel_id or None

		channels['default.channel'] = default_channel

		items = PremiumGuildConfig.objects.filter(guild=self)
		for item in items:
			if item.key.endswith('.channel'):
				channels[item.key] = '<#%s>' % item.value

		for key in PremiumGuildConfig.MESSAGE_FORMATS.keys():
			channel_key = '%s.channel' % key
			if channel_key not in channels:
				channels[channel_key] = default_channel

		return channels

	def get_formats(self):

		formats = {}

		items = PremiumGuildConfig.objects.filter(guild=self)
		for item in items:
			if item.key.endswith('.format'):
				formats[item.key] = item.value

		for key, fmt in PremiumGuildConfig.MESSAGE_FORMATS.items():
			format_key = '%s.format' % key
			if format_key not in formats:
				formats[format_key] = fmt

		return formats

	def get_mentions(self):

		mentions = {}

		default_mention = '**Off**'

		items = PremiumGuildConfig.objects.filter(guild=self)
		for item in items:
			if item.key.endswith('.mention'):
				mentions[item.key] = '<!@%s>' % item.value

		for key in PremiumGuildConfig.MESSAGE_FORMATS.keys():
			mention_key = '%s.mention' % key
			if mention_key not in mentions:
				mentions[mention_key] = default_mention

		return mentions

class PremiumGuildConfig(models.Model):

	MSG_SQUAD_ARENA_UP             = 'arena.squad.up'
	MSG_SQUAD_ARENA_DOWN           = 'arena.squad.down'
	MSG_SQUAD_ARENA_RANK_MAX       = 'arena.squad.rank.max'
	MSG_FLEET_ARENA_UP             = 'arena.fleet.up'
	MSG_FLEET_ARENA_DOWN           = 'arena.fleet.down'
	MSG_FLEET_ARENA_RANK_MAX       = 'arena.fleet.rank.max'
	MSG_INACTIVITY                 = 'inactivity'
	MSG_INACTIVITY_MIN             = 'inactivity.min'
	MSG_INACTIVITY_REPEAT          = 'inactivity.repeat'
	MSG_PLAYER_LEVEL               = 'player.level'
	MSG_PLAYER_LEVEL_MIN           = 'player.level.min'
	MSG_PLAYER_NICK                = 'player.nick'
	MSG_UNIT_UNLOCKED              = 'unit.unlocked'
	MSG_UNIT_LEVEL                 = 'unit.level'
	MSG_UNIT_LEVEL_MIN             = 'unit.level.min'
	MSG_UNIT_OMEGA                 = 'unit.omega'
	MSG_UNIT_RARITY                = 'unit.rarity'
	MSG_UNIT_RARITY_MIN            = 'unit.rarity.min'
	MSG_UNIT_RELIC                 = 'unit.relic'
	MSG_UNIT_RELIC_MIN             = 'unit.relic.min'
	MSG_UNIT_GEAR_LEVEL            = 'unit.gear'
	MSG_UNIT_GEAR_LEVEL_MIN        = 'unit.gear.min'
	MSG_UNIT_GEAR_PIECE            = 'unit.gear.piece'
	MSG_UNIT_ZETA                  = 'unit.zeta'
	MSG_UNIT_SKILL_UNLOCKED        = 'skill.unlocked'
	MSG_UNIT_SKILL_INCREASED       = 'skill.increased'
	MSG_UNIT_SKILL_INCREASED_MIN   = 'skill.increased.min'

	MESSAGE_DEFAULTS = [

		(MSG_SQUAD_ARENA_UP,           True, bool),
		(MSG_SQUAD_ARENA_DOWN,         True, bool),
		(MSG_SQUAD_ARENA_RANK_MAX,     10000, int),
		(MSG_FLEET_ARENA_UP,           True, bool),
		(MSG_FLEET_ARENA_DOWN,         True, bool),
		(MSG_FLEET_ARENA_RANK_MAX,     10000, int),
		(MSG_INACTIVITY,               True, bool),
		(MSG_INACTIVITY_MIN,           48,   int),
		(MSG_INACTIVITY_REPEAT,        24,   int),
		(MSG_PLAYER_LEVEL,             True, bool),
		(MSG_PLAYER_LEVEL_MIN,         0,    int),
		(MSG_PLAYER_NICK,              True, bool),
		(MSG_UNIT_UNLOCKED,            True, bool),
		(MSG_UNIT_LEVEL,               True, bool),
		(MSG_UNIT_LEVEL_MIN,           0,    int),
		(MSG_UNIT_OMEGA,               True, bool),
		(MSG_UNIT_RARITY,              True, bool),
		(MSG_UNIT_RARITY_MIN,          0,    int),
		(MSG_UNIT_RELIC,               True, bool),
		(MSG_UNIT_RELIC_MIN,           0,    int),
		(MSG_UNIT_GEAR_LEVEL,          True, bool),
		(MSG_UNIT_GEAR_LEVEL_MIN,      0,    int),
		(MSG_UNIT_GEAR_PIECE,          True, bool),
		(MSG_UNIT_ZETA,                True, bool),
		(MSG_UNIT_SKILL_UNLOCKED,      True, bool),
		(MSG_UNIT_SKILL_INCREASED,     True, bool),
		(MSG_UNIT_SKILL_INCREASED_MIN, 0,    int),
	]

	MESSAGE_FORMATS = {

		MSG_INACTIVITY:           '${nick} has been inactive for ${last.seen}',
		MSG_PLAYER_NICK:          '${nick} is now known as ${new.nick}',
		MSG_PLAYER_LEVEL:         '${nick} reached level ${level}',
		MSG_UNIT_UNLOCKED:        '${nick} unlocked ${unit}',
		MSG_UNIT_LEVEL:           '${nick} increased ${unit} to level ${level}',
		MSG_UNIT_RARITY:          '${nick} promoted ${unit} to ${rarity} stars',
		MSG_UNIT_RELIC:           '${nick} increased ${unit} to relic ${relic}',
		MSG_UNIT_GEAR_LEVEL:      '${nick} increased ${unit}\'s gear to level ${gear.level.roman}',
		MSG_UNIT_GEAR_PIECE:      '${nick} set equipment ${gear.piece} on ${unit}',
		MSG_UNIT_SKILL_UNLOCKED:  '${nick} unlocked ${unit}\'s skill ${skill}',
		MSG_UNIT_SKILL_INCREASED: '${nick} increased skill ${skill} to tier ${tier} (${unit})',
		MSG_UNIT_OMEGA:           '${nick} applied **Omega** upgrade to ${skill} (${unit})',
		MSG_UNIT_ZETA:            '${nick} applied **Zeta** upgrade to ${skill} (${unit})',
		MSG_SQUAD_ARENA_UP:       '${nick} has _climbed up_ in squad arena __**${old.rank} => ${new.rank}**__',
		MSG_SQUAD_ARENA_DOWN:     '${nick} has _dropped down_ in squad arena __**${old.rank} => ${new.rank}**__',
		MSG_FLEET_ARENA_UP:       '${nick} has _climbed up_ in fleet arena __**${old.rank} => ${new.rank}**__',
		MSG_FLEET_ARENA_DOWN:     '${nick} has _dropped down_ in fleet arena __**${old.rank} => ${new.rank}**__',
	}

	guild = models.ForeignKey(PremiumGuild, on_delete=models.CASCADE)
	key = models.CharField(max_length=32)
	value = models.CharField(max_length=32)
	value_type = models.CharField(max_length=4)

	def get_categories():

		categories = [ '`all` or `*`' ]

		for key, value in sorted(PremiumGuildConfig.MESSAGE_FORMATS.items()):

			category = '`%s`' % key.split('.', 1)[0]
			if category not in categories:
				categories.append(category)

		return categories

	def get_types():

		types = {}

		for key, val, typ in PremiumGuildConfig.MESSAGE_DEFAULTS:
			types[key] = typ.__name__

		return types
