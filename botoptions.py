import re
import pytz
import logging
from datetime import datetime

from utils import basicstrip, get_available_timezones, is_supported_timezone

import DJANGO
from swgoh.models import Player, BaseUnit, BaseUnitFaction

MODSET_OPTS = {
	'he':             'Health',
	'health':         'Health',
	'de':             'Defense',
	'defense':        'Defense',
	'po':             'Potency',
	'potency':        'Potency',
	'te':             'Tenacity',
	'tenacity':       'Tenacity',
	'cc':             'Critical Chance',
	'criticalchance': 'Critical Chance',
	'cd':             'Critical Damage',
	'criticaldamage': 'Critical Damage',
	'of':             'Offense',
	'offense':        'Offense',
	'sp':             'Speed',
	'speed':          'Speed',
}

MODSLOTS_OPTS = {
	'sq':       1,
	'square':   1,
	'ar':       2,
	'arrow':    2,
	'di':       3,
	'diamond':  3,
	'tr':       4,
	'triangle': 4,
	'ci':       5,
	'circle':   5,
	'cr':       6,
	'cross':    6,
}

MODPRIMARIES_OPTS = {
	'ac':                'Accuracy',
	'accuracy':          'Accuracy',
	'ca':                'Critical Avoidance',
	'criticalavoidance': 'Critical Avoidance',
	'cc':                'Critical Chance',
	'criticalchance':    'Critical Chance',
	'cd':                'Critical Damage',
	'criticaldamage':    'Critical Damage',
	'de':                'Defense',
	'defense':           'Defense',
	'he':                'Health',
	'health':            'Health',
	'of':                'Offense',
	'offense':           'Offense',
	'po':                'Potency',
	'potency':           'Potency',
	'pr':                'Protection',
	'protection':        'Protection',
	'sp':                'Speed',
	'speed':             'Speed',
	'te':                'Tenacity',
	'tenacity':          'Tenacity',
}

class BotOptions:

	def __init__(self, bot):
		self.bot = bot
		self.config = bot.config
		self.errors = bot.errors
		self.redis = bot.redis

	def parse_premium_user(self, author):

		try:
			return Player.objects.get(discord_id=author.id)

		except Player.DoesNotExist:
			return None

	def parse_integer(self, args):

		selected_value = None
		args_cpy = list(args)
		for arg in args_cpy:

			try:
				selected_value = int(arg)
				args.remove(arg)

			except:
				pass

		return selected_value

	def parse_ally_code(self, arg):
		regex = r'^[0-9]{9}$|^[0-9]{3}-[0-9]{3}-[0-9]{3}$'
		m = re.search(regex, arg)
		return m and int(m.group(0).replace('-', '')) or False

	def parse_ally_code_excluded(self, arg):
		regex = r'^-([0-9]{9}$|[0-9]{3}-[0-9]{3}-[0-9]{3})$'
		m = re.search(regex, arg)
		return m and int(m.group(1).replace('-', '')) or False

	def parse_ally_codes(self, args):

		ally_codes = []
		args_cpy = list(args)
		for arg in args_cpy:

			ally_code = self.parse_ally_code(arg)
			if ally_code:
				args.remove(arg)
				if ally_code not in ally_codes:
					ally_codes.append(ally_code)

		return ally_codes

	def parse_ally_codes_excluded(self, args):

		excluded = []
		args_cpy = list(args)
		for arg in args_cpy:

			ally_code = self.parse_ally_code_excluded(arg)
			if ally_code:
				args.remove(arg)
				if ally_code not in excluded:
					excluded.append(ally_code)

		return excluded

	def parse_mentions(self, ctx, args):

		discord_ids = []
		author = ctx.author
		args_cpy = list(args)
		for arg in args_cpy:

			discord_id = None

			m = re.search(r'^<@!?([0-9]+)>$', arg)
			if m:
				args.remove(arg)
				discord_id = int(m.group(1))
				if discord_id not in discord_ids:
					discord_ids.append(discord_id)

			elif arg.lower() in [ 'me', '@me' ]:
				args.remove(arg)
				if author.id not in discord_ids:
					discord_ids.append(author.id)

			elif arg.startswith('@'):
				p = Player.get_player_by_nick(arg[1:])
				if p:
					args.remove(arg)
					if p.discord_id not in discord_ids:
						discord_ids.append(p.discord_id)

		return discord_ids

	def parse_players(self, ctx, args, min_allies=1, max_allies=-1, expected_allies=1, exclude_author=False, language='eng_us'):

		discord_ids = self.parse_mentions(ctx, args)
		ally_codes = self.parse_ally_codes(args)

		players = []
		unregistered = []
		for discord_id in discord_ids:

			try:
				p = Player.objects.get(discord_id=discord_id)

				if p not in players:
					players.append(p)

				if p.ally_code not in ally_codes:
					ally_codes.append(p.ally_code)

			except Player.DoesNotExist:
				unregistered.append(discord_id)

		if unregistered:
			return None, self.errors.ally_codes_not_registered(ctx, unregistered)

		if exclude_author is False:

			if (not discord_ids and not ally_codes) or len(ally_codes) < min_allies or len(ally_codes) < expected_allies:
				try:
					p = Player.objects.get(discord_id=ctx.author.id)

					if p not in players:
						players.insert(0, p)

					if p.ally_code not in ally_codes:
						ally_codes.insert(0, p.ally_code)

				except Player.DoesNotExist:
					pass

		elif not ally_codes:
			return [], None

		if not ally_codes:
			return None, self.errors.no_ally_code_specified(ctx)

		if len(ally_codes) < min_allies:
			return None, self.errors.not_enough_ally_codes_specified(ally_codes, min_allies)

		if len(ally_codes) > max_allies and max_allies != -1:
			return None, self.errors.too_many_ally_codes_specified(ally_codes, max_allies)

		for ally_code in ally_codes:

			queryset = Player.objects.filter(ally_code=ally_code)
			if queryset.count() > 0:
				player = queryset.first()
			else:
				player = Player(ally_code=ally_code)

			if player not in players:
				players.append(player)

			if player.banned:
				guild = ctx.channel.guild
				guild_id = hasattr(guild, 'id') and guild.id or None
				origin = '[%s <@%s>][#%s <@%s>][%s <@%s>]' % (guild, guild_id, ctx.channel, ctx.channel.id, ctx.author, ctx.author.id)
				logger = logging.getLogger('opts')
				logger.log(logging.INFO, '%s: Detected usage of blacklisted allycode: %s' % (origin, player.ally_code))

		return players, None

	def parse_unit_names_by_faction(self, arg):

		faction = []

		larg = basicstrip(arg.lower())
		if larg in BaseUnitFaction.FACTION_NICKS:
			larg = BaseUnitFaction.FACTION_NICKS[larg]

		for fac_key, fac_name in BaseUnitFaction.FACTIONS:
			if larg in fac_key.split('_'):
				if fac_key not in faction:
					faction.append(fac_key)
				break

		return BaseUnit.get_units_by_faction(faction)

	def parse_unit_names_broad(self, args, units):

		full_match = []
		token_match = []
		wild_match = []
		loose_match = []

		if not args:
			return None

		arg = basicstrip(' '.join(args))

		faction = self.parse_unit_names_by_faction(arg)
		if faction:
			return faction

		for unit in units:

			if arg in self.config['nicks']:
				arg = basicstrip(self.config['nicks'][arg])

			name = basicstrip(unit.name)

			if arg == name:
				full_match.append(unit)

			elif arg in name.split('-') or arg in name.split(' '):
				token_match.append(unit)

			elif arg in name or arg in name.replace('-', '').replace(' ', ''):
				wild_match.append(unit)

			elif arg.replace('-', '') == name.replace('-', ''):
				loose_match.append(unit)

		if full_match:
			return full_match

		if token_match:
			return token_match

		if wild_match:
			return wild_match

		if loose_match:
			return loose_match

		return None

	def parse_unit_names(self, args):

		if not args:
			return []

		units = BaseUnit.objects.all()

		match = self.parse_unit_names_broad(args, units)
		if match:
			args.clear()
			return match

		selected_units = []
		args_cpy = list(args)

		for arg in args_cpy:

			nick = basicstrip(arg)
			if nick in self.config['nicks']:
				nick = basicstrip(self.config['nicks'][nick])

			match = self.parse_unit_names_broad([ nick ], units)
			if match:
				args.remove(arg)
				for m in match:
					if m not in selected_units:
						selected_units.append(m)

		return selected_units

	def parse_unit_names_v1(self, args):

		selected_units = []
		new_args = list(args)

		for arg in new_args:

			if len(arg) < 2:
				continue

			larg = basicstrip(arg)
			if larg in self.config['nicks']:
				larg = basicstrip(self.config['nicks'][larg])

			found = False
			units = BaseUnit.objects.all()

			new_units = []
			for unit in units:

				name1 = basicstrip(unit.name)
				name2 = name1.replace('î', 'i').replace('Î', 'i')
				name3 = name1.replace('-', '')
				name4 = name1.replace('\'', '')

				if larg in name1 or larg in name2 or larg in name3 or larg in name4:
					found = True
					new_units.append(unit)
					if larg == name1:
						new_units = [ unit ]
						break

			if found:
				args.remove(arg)
				selected_units.extend(new_units)

		return selected_units

	def parse_char_filters(self, args):

		selected_char_filters = {
			'gp':     1,
			'gear':   1,
			'level':  1,
			'rarity': 1,
			'relic':  0,
		}

		rules = {
			'gp':     r'^(gp)([0-9]+)$',
			'gear':   r'^(g|gear|gears)([0-9]+)$',
			'level':  r'^(l|level|levels)([0-9]+)$',
			'rarity': r'^(s|star|stars|rarity)([0-9]+)$',
			'relic':  r'^(r|relic|relics)([0-9]+)$',
			'stars':  r'^([0-9]+)(\*|s|star|stars)$',
		}

		args_cpy = list(args)
		for arg in args_cpy:
			for key, regex in rules.items():
				m = re.search(regex, arg)
				if m:
					args.remove(arg)

					group_index = 2
					if key == 'stars':
						group_index = 1
						key = 'rarity'

					selected_char_filters[key] = int(m.group(group_index))

		return selected_char_filters

	def parse_modsets(self, args, ref_table):

		selected_modsets = []
		args_cpy = list(args)
		for arg in args_cpy:
			if arg in ref_table:
				args.remove(arg)
				modset = ref_table[arg]
				if modset not in selected_modsets:
					selected_modsets.append(modset)

		return selected_modsets

	def parse_modslots(self, args):

		selected_modslots = []
		args_cpy = list(args)
		for arg in args_cpy:
			if arg in MODSLOTS_OPTS:
				args.remove(arg)
				modslot = MODSLOTS_OPTS[arg]
				if modslot not in selected_modslots:
					selected_modslots.append(modslot)

		return selected_modslots

	def parse_modprimaries(self, args):

		selected_primaries = []
		args_cpy = list(args)
		for arg in args_cpy:
			if arg in MODPRIMARIES_OPTS:
				args.remove(arg)
				modprimary = MODPRIMARIES_OPTS[arg]
				if modprimary not in selected_primaries:
					selected_primaries.append(modprimary)

		return selected_primaries

	def parse_mod_filters(self, args):

		selected_filters = []
		args_cpy = list(args)
		for arg in args_cpy:
			toks = arg.split('/')
			if len(toks) == 3:
				modsets = self.parse_modsets([ toks[0] ], MODSET_OPTS)
				slots   = self.parse_modslots([ toks[1] ])
				prims   = self.parse_modprimaries([ toks[2] ])
				if modsets and slots and prims:
					tupl = (modsets[0], slots[0], prims[0])
					if tupl not in selected_filters:
						args.remove(arg)
						selected_filters.append(tupl)

		return selected_filters

	def parse_lang(self, ctx, args):

		author = ctx.author
		# TODO: try to parse language from args

		try:
			p = Player.objects.get(discord_id=author.id)
			return p.language

		except Player.DoesNotExist:
			pass

		return 'eng_us'

	def parse_language(self, args):

		args_cpy = list(args)
		for arg in args_cpy:

			argl = arg.lower()
			language = Player.get_language_info(argl)
			if language is not None:
				args.remove(arg)
				return language

		return None

	def parse_timezones(self, args):

		timezones = []
		all_timezones = get_available_timezones()

		args_cpy = list(args)
		for arg in args_cpy:

			larg = arg.lower()
			tz = is_supported_timezone(larg, all_timezones)
			if tz:
				args.remove(arg)
				if tz not in timezones:
					timezones.append(tz)

		larg = '_'.join(args).lower()
		tz = is_supported_timezone(larg, all_timezones)
		if tz:
			args.clear()
			if tz not in timezones:
				timezones.append(tz)

		return timezones

	def parse_meta(self, args):

		top_n = 5
		selected_opts = []
		args_cpy = list(args)

		opts_meta = {
			'a':             'arena',
			'arena':         'arena',
			'f':             'fleet',
			'fleet':         'fleet',
			'l':             'leader',
			'leader':        'leader',
			'c':             'commander',
			'commander':     'commander',
			'C':             'compact',
			'compact':       'compact',
			'r':             'reinforcement',
			'reinforcement': 'reinforcement',

		}

		for arg in args_cpy:

			if arg in opts_meta:
				args.remove(arg)
				opt = opts_meta[arg]
				selected_opts.append(opt)

			elif arg.isdigit():
				args.remove(arg)
				arg = int(arg)
				if arg < 1:
					arg = 1
				if arg > 50:
					arg = 50

				top_n = int(arg)

		return selected_opts, top_n

	def parse_limit(self, args, default=25):

		args_cpy = list(args)
		for arg in args_cpy:
			try:
				limit = int(arg)
				args.remove(arg)
				return limit

			except:
				pass

		return default

	def parse_include_locked(self, args):

		args_cpy = list(args)
		for arg in args_cpy:

			larg = arg.lower()
			if larg == 'locked' or larg == 'l':
				args.remove(arg)
				return True

		return False

	def parse_tier(self, args):

		tier = None
		args_cpy = list(args)
		for arg in args_cpy:
			if arg.lower() == 'max':
				args.remove(arg)
				return 'max'

			try:
				tier = int(arg)
				args.remove(arg)
				break
			except:
				pass

		return tier

	def parse_skill_types(self, args):

		types = {}

		skill_types = {
			'b':        'basicability',
			'basic':    'basicability',
			'c':        'contractability',
			'contract': 'contractability',
			'h':        'hardwareability',
			'hw':       'hardwareability',
			'hardware': 'hardwareability',
			'l':        'leaderability',
			'leader':   'leaderability',
			's':        'specialability',
			'special':  'specialability',
			'u':        'uniqueability',
			'unique':   'uniqueability',
		}

		args_cpy = list(args)
		for arg in args_cpy:

			larg = arg.lower()
			if larg in skill_types:
				skill_type = skill_types[larg]
				args.remove(arg)
				if skill_type not in types:
					types[skill_type] = -1
			else:
				for a_skill_type in skill_types:
					pattern = r'^%s(\d+)$' % a_skill_type
					match = re.search(pattern, larg)
					if match:
						args.remove(arg)
						skill_type = skill_types[a_skill_type]
						types[skill_type] = int(match.group(1))
						break

		return types and types or {
			'basicability': -1,
			'contractability': -1,
			'hardwareability': -1,
			'leaderability': -1,
			'specialability': -1,
			'uniqueability': -1,
		}

	def parse_modcheck(self, args):

		actions = []
		args_cpy = list(args)
		for arg in args_cpy:

			larg = arg.lower()

			if larg in [ 'c', 'count' ]:
				args.remove(arg)
				actions.append('count')

			elif larg in [ 'n', 'nm', 'nomods' ]:
				args.remove(arg)
				actions.append('missing')

			elif larg in [ 'm', 'miss', 'missing' ]:
				args.remove(arg)
				actions.append('missing')

			elif larg in [ 'i', 'inc', 'incomplete' ]:
				args.remove(arg)
				actions.append('incomplete')

			elif larg in [ 'l', 'lvl', 'level' ]:
				args.remove(arg)
				actions.append('level')

			elif larg in [ '5', '5p', '5pip', '5pips', '5-pips' ]:
				args.remove(arg)
				actions.append('5pips')

			elif larg in [ '6', '6p', '6pip', '6pips', '6-pips' ]:
				args.remove(arg)
				actions.append('6pips')

			elif larg in [ 't', 'tier', 'tiers', 'color' ]:
				args.remove(arg)
				actions.append('tier')

		return actions and actions or [
			'count',
			'missing',
			#'nomods',
			'incomplete',
			'level',
			'5pips',
			#'6pips',
			#'tier',
		]

	def parse_min_gear_level(self, args, default=9):

		args_cpy = list(args)
		for arg in args_cpy:

			larg = arg.lower()
			match = re.search(r'^(gear|g)([0-9]{1,2})$', larg)
			if match:
				args.remove(arg)
				return int(match.group(2))

		return default

	def parse_locked(self, args):

		opts = []
		args_cpy = list(args)

		opts_locked = {
			'c':     'chars',
			'chars': 'chars',
			's':     'ships',
			'ships': 'ships',
		}

		for arg in args_cpy:

			if arg in opts_locked:
				args.remove(arg)
				opt = opts_locked[arg]
				if opt not in opts:
					opts.append(opt)

		if not opts or len(opts) >= 2:
			opts = 'all'
		else:
			opts = opts.pop(0)

		return opts

	def parse_arena(self, args):

		selected_opts = 'chars'
		args_cpy = list(args)

		opts_arena = {
			'c':     'chars',
			'char':  'chars',
			'chars': 'chars',
			's':     'ships',
			'ship':  'ships',
			'ships': 'ships',
			'f':     'ships',
			'fleet': 'ships',
		}

		for arg in args_cpy:

			if arg in opts_arena:
				args.remove(arg)
				opt = opts_arena[arg]
				return opt

		return selected_opts

	def parse_format(self, args):

		args_cpy = list(args)

		for arg in args_cpy:

			if arg in self.config['formats']:
				args.remove(arg)
				return self.config['formats'][arg]

			elif arg in [ 'c', 'custom' ]:
				args.remove(arg)
				fmt = next(args_cpy)
				args.remove(fmt)
				return fmt

		return '**%name** (%role)\n**GP**: %gp **Level**: %level **Gear**: %gear **Health**: %health **Protection**: %protection **Speed**: %speed\n**Potency**: %potency **Tenacity**: %tenacity **CD**: %critical-damage **CC (phy)**: %physical-critical-chance **CC (spe)**: %special-critical-chance\n**Armor**: %armor **Resistance**: %resistance\n'

	def parse_relic_tier(self, args, max_relic=7):

		args_cpy = list(args)
		for arg in args_cpy:

			try:
				relic = int(arg)
				args.remove(arg)
				return relic

			except:
				pass

		return max_relic

	def parse_auto(self, args):

		args_cpy = list(args)
		for arg in args_cpy:
			if arg.lower() == 'auto':
				args.remove(arg)
				return True

		return False

	def parse_shard_type(self, args):

		args_cpy = list(args)
		for arg in args_cpy:

			larg = arg.lower()
			if larg in shard_types:
				args.remove(arg)
				return shard_types[larg]

		return None

	def parse_payout_time(self, tz, args):

		import re

		args_cpy = list(args)

		for arg in args_cpy:
			result = re.match('^[0-9]{1,2}[:h][0-9]{1,2}$', arg)
			if result:
				args.remove(arg)
				now = datetime.now(tz)
				tokens = result[0].replace('h', ':').split(':')
				return now.replace(hour=int(tokens[0]), minute=int(tokens[1]), second=0, microsecond=0).astimezone(pytz.utc)

		return None

