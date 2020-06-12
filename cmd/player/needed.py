import traceback

from utils import roundup, get_banner_emoji, get_field_legend, extract_modstats, extract_modstats_from_roster
from constants import EMOJIS, MODSETS, MODSLOTS, MODSPRIMARIES

import DJANGO

from swgoh.models import ModRecommendation

help_needed = {
	'title': 'Needed Help',
	'description': """Shows statistics about recommended mod sets and mod primaries according to EA / Capital Games, Crouching Rancor, and swgoh.gg's mod meta reports.

**Syntax**
```
%prefixneeded```
**Aliases**
```
%prefixn```
**Examples**
```
%prefixn```"""
}

def pad_numbers(count):
	return max(0, 3 - len(str(count))) * '\u00a0'

def get_field_modset_stats(config):

	modsets = {}
	spacer = EMOJIS['']
	sources = ModRecommendation.objects.all().values('source').distinct()
	sources = [ x['source'] for x in sources ]
	src_emojis = []
	for source in sources:
		emoji_key = source.replace(' ', '').lower()
		if emoji_key in EMOJIS:
			src_emojis.append(EMOJIS[emoji_key])

	headers = [ '%s%s' % (spacer, '|'.join(src_emojis)) ]

	result = {}
	recos = ModRecommendation.objects.all()
	for reco in recos:
		source = reco.source
		if source not in result:
			result[source] = {}

		char_id = reco.character_id
		if char_id not in result[source]:
			result[source][char_id] = []

		result[source][char_id].append(reco)

	for source, names in result.items():

		new_modsets = {}
		for name, recos in names.items():

			amount = len(recos)
			for reco in recos:

				sets = [ reco.set1, reco.set2, reco.set3 ]

				for aset in sets:
					if aset not in new_modsets:
						new_modsets[aset] = 0.0
					new_modsets[aset] += 1.0 / amount

		lines = []
		for aset, count in new_modsets.items():

			if aset not in modsets:
				modsets[aset] = {}

			if source not in modsets[aset]:
				modsets[aset][source] = 0.0

			modsets[aset][source] += count

		for aset_name in MODSETS.values():
			if aset_name not in modsets:
				continue

			counts = []
			sources = modsets[aset_name]
			for source, count in sorted(sources.items()):
				modset_emoji = EMOJIS[ aset_name.replace(' ', '').lower() ]
				count = roundup(count)
				pad = pad_numbers(count)
				counts.append('%s%d' % (pad, count))

			if len(counts) < 3:
				pad = pad_numbers(0)
				counts.append('%s%d' % (pad, 0))

			lines.append('%s `|%s`' % (modset_emoji, '|'.join(counts)))

	lines.append(config['separator'])

	lines = headers + lines

	return {
		'name': '== Needed Mod Sets ==',
		'value': '\n'.join(lines),
		'inline': True,
	}

def get_field_primary_stats(config, profile, selected_slots, selected_primaries):

	spacer = EMOJIS['']

	if not selected_slots:
		selected_slots = MODSLOTS.values()

	if not selected_primaries:
		selected_primaries = MODSPRIMARIES

	result = {}
	recos = ModRecommendation.objects.all().values()
	for reco in recos:
		char_id = reco['character_id']
		if char_id not in result:
			result[char_id] = []

		result[char_id].append(reco)

	stats = {}

	for unit, recos in result.items():
		extract_modstats(stats, recos)

	player_stats = {}
	extract_modstats_from_roster(player_stats, profile['roster'])

	lines = []
	for slot in selected_slots:
		slot = slot.lower()
		slot_emoji = EMOJIS[slot]
		if slot not in stats:
			continue

		sublines = []
		for primary in sorted(selected_primaries):
			if primary in stats[slot]:
				cg_count = 0
				if 'Capital Games' in stats[slot][primary]:
					cg_count = roundup(stats[slot][primary]['Capital Games'])

				cr_count = 0
				if 'Crouching Rancor' in stats[slot][primary]:
					cr_count = roundup(stats[slot][primary]['Crouching Rancor'])

				gg_count = 0
				if 'swgoh.gg' in stats[slot][primary]:
					gg_count = roundup(stats[slot][primary]['swgoh.gg'])

				ally_count = 0
				if slot in player_stats and primary in player_stats[slot]:
					ally_count = player_stats[slot][primary]

				pad1 = pad_numbers(cg_count)
				pad2 = pad_numbers(cr_count)
				pad3 = pad_numbers(gg_count)
				pad4 = pad_numbers(ally_count)

				sublines.append('%s `|%s%d|%s%d|%s%d|%s%d|%s`' % (slot_emoji, pad1, cg_count, pad2, cr_count, pad3, gg_count, pad4, ally_count, primary))

		if sublines:
			lines += [ config['separator'] ] + sublines

	sources = ModRecommendation.objects.all().values('source').distinct()
	sources = [ x['source'] for x in sources ]

	emojis = []
	for source in sources:
		emoji_key = source.replace(' ', '').lower()
		if emoji_key in EMOJIS:
			emojis.append(EMOJIS[emoji_key])

	guild_logo = 'guildBannerLogo' in profile and profile['guildBannerLogo'] or None
	emojis.append(get_banner_emoji(guild_logo))

	lines = [
		'%s\u202F\u202F\u202F%s`|Primary Stats`' % (spacer, '|'.join(emojis)),
	] + lines

	return '\n'.join(lines)

async def cmd_needed(ctx):

	bot = ctx.bot
	args = ctx.args
	config = ctx.config

	ctx.alt = bot.options.parse_alt(args)
	selected_players, error = bot.options.parse_players(ctx, args)

	selected_slots = bot.options.parse_modslots(args)

	selected_primaries = bot.options.parse_modprimaries(args)

	emoji_cg = EMOJIS['capitalgames']
	emoji_cr = EMOJIS['crouchingrancor']
	emoji_gg = EMOJIS['swgoh.gg']

	if error:
		return error

	if args:
		return bot.errors.unknown_parameters(args)

	if not selected_players:
		return bot.errors.no_ally_code_specified(ctx)

	msgs = []
	ally_codes = [ player.ally_code for player in selected_players ]
	players = await bot.client.players(ally_codes=ally_codes)
	if not players:
		return bot.errors.ally_code_not_found(ally_codes)

	players = { x['allyCode']: x for x in players }

	for player in selected_players:

		ally_code = player.ally_code
		profile = players[ally_code]

		field_primary_stats = get_field_primary_stats(config, profile, selected_slots, selected_primaries)
		field_modset_stats  = get_field_modset_stats(config)
		field_legend        = get_field_legend(config)

		msgs.append({
			'title': '== Needed Mod Primaries ==',
			'description': field_primary_stats,
			'fields': [
				field_modset_stats,
				field_legend,
			],
		})

	return msgs
