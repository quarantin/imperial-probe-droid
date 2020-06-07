from discord.ext import commands

import cog
from utils import basicstrip, get_banner_emoji, get_mod_sets_emojis, get_mod_primaries, get_field_legend, translate
from swgohgg import get_full_avatar_url, get_swgohgg_unit_url
from constants import EMOJIS

import DJANGO
from swgoh.models import ModRecommendation

class Recos(cog.Cog):

	help_title = 'Recos Help'
	help_description = """Shows recommended mods from Capital Games, Crouching Rancor and swgoh.gg meta report.

__**Syntax**__
```
%prefixrecos [players] [characters]```
__**Aliases**__
```
%prefixr```
__**Examples**__
Show recommended mods for **Darth Revan**:
```
%prefixr darth revan```"""

	def get_short_stat(self, stat_id, language):

		stat_id = stat_id.strip()

		stat_name = stat_id
		if stat_name not in [ 'Critical Avoidance', 'Critical Chance', 'Critical Damage' ]:
			stat_name = translate(stat_name, language)

		tokens = stat_name.split(' ')
		if len(tokens) == 1:
			return tokens[0][0:2]

		elif len(tokens) == 2:
			return '%s%s' % (tokens[0][0], tokens[1][0])

		raise Exception('Invalid short stat request for %s %s (%s)' % (stat_id, language, stat_name))

	@commands.command(aliases=[ 'r', 'reco' ])
	async def recos(self, ctx, *, args: list = []):

		emoji_cg = EMOJIS['capitalgames']
		emoji_cr = EMOJIS['crouchingrancor']
		emoji_gg = EMOJIS['swgoh.gg']

		language = self.options.parse_lang(ctx, args)

		selected_players, error = self.options.parse_players(ctx, args)

		selected_units = self.options.parse_unit_names(args)
		print('WTF:')
		print(selected_units)
		import sys
		sys.exit()

		if error:
			return error

		if not selected_players:
			return self.errors.no_ally_code_specified(ctx)

		if not selected_units:
			return self.errors.no_unit_selected(ctx)

		if args:
			return self.errors.unknown_parameters(args)

		ally_codes = [ player.ally_code for player in selected_players ]
		players = await self.client.players(ally_codes=ally_codes)
		if not players:
				return self.errors.ally_codes_not_found(ally_codes)

		players = { x['allyCode']: x for x in players }

		embeds = []
		for player in selected_players:

			player_data = players[player.ally_code]
			guild_banner = get_banner_emoji(player_data['guildBannerLogo'])
			discord_id = player.discord_id and '<@%s>' % player.discord_id or player.player_name

			lines  = []
			for ref_unit in selected_units:

				lines.clear()

				base_id   = ref_unit.base_id
				unit_name = translate(base_id, language)

				if ref_unit.is_ship:
					continue

				roster = { x['defId']: x for x in player_data['roster'] }
				recos  = ModRecommendation.objects.filter(character_id=ref_unit.id).values()

				for reco in recos:

					source   = EMOJIS[ reco['source'].replace(' ', '').lower() ]

					set1     = EMOJIS[ reco['set1'].replace(' ', '').lower() ]
					set2     = EMOJIS[ reco['set2'].replace(' ', '').lower() ]
					set3     = EMOJIS[ reco['set3'].replace(' ', '').lower() ]

					square   = self.get_short_stat(reco['square'],   language)
					arrow    = self.get_short_stat(reco['arrow'],    language)
					diamond  = self.get_short_stat(reco['diamond'],  language)
					triangle = self.get_short_stat(reco['triangle'], language)
					circle   = self.get_short_stat(reco['circle'],   language)
					cross    = self.get_short_stat(reco['cross'],    language)

					info     = reco['info'].strip()
					info     = info and ' %s' % info or ''

					line = '%s%s%s%s`%s|%s|%s|%s`%s' % (source, set1, set2, set3, arrow, triangle, circle, cross, info)
					lines.append(line)

				if base_id in roster and 'mods' in roster[base_id]:
					unit = roster[base_id]
					spacer = EMOJIS['']
					modsets = get_mod_sets_emojis(self.config, unit['mods'])
					primaries = get_mod_primaries(self.config, unit['mods'])
					del(primaries[1])
					del(primaries[3])

					primaries = [ primaries[x] for x in primaries ]

					source   = guild_banner

					set1     = modsets[0]
					set2     = modsets[1]
					set3     = modsets[2]

					short_primaries = []
					for primary in primaries:
						short_primaries.append(self.get_short_stat(primary, language))

					primaries = '|'.join(short_primaries)

					line = '%s%s%s%s`%s` %s' % (source, set1, set2, set3, primaries, discord_id)

				elif base_id not in roster:
					unit = None
					line = '**%s** is still locked for %s' % (unit_name, discord_id)

				else:
					unit = roster[base_id]
					line = '**%s** has no mods for %s' % (unit_name, discord_id)

				lines.append(self.config['separator'])
				lines.append(line)

				spacer = EMOJIS[''] * 4

				header = '%s%s%s%s%s' % (spacer, EMOJIS['arrow'], EMOJIS['triangle'], EMOJIS['circle'], EMOJIS['cross'])
				unit_link = '**[%s](%s)**' % (unit_name, get_swgohgg_unit_url(ref_unit.base_id))

				for line in [ header, self.config['separator'], unit_link ]:
					lines.insert(0, line)

				embeds.append({
					'title': '',
					'description': '\n'.join(lines),
					'author': {
						'name': ref_unit.name,
						'icon_url': ref_unit.get_image(),
					},
					'image': {
						'url': get_full_avatar_url(self.config, ref_unit, unit),
					},
					'fields': [ get_field_legend(self.config) ],
				})

			if not lines:
				embeds.append({
					'title': '== No Recommended Mod Sets ==',
					'description': '**%s** is missing from all source of recommendations.' % unit_name,
				})

		await self.bot.send_embed(ctx, embeds)
