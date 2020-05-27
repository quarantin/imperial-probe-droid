from discord.ext import commands

import cog

class Help(cog.Cog):

	tokens = [
			'authors',
			'discord',
			'invite',
			'patreon',
			'prefix',
			'separator',
			'source',
	]

	help_title = 'Imperial Probe Droid Help - Prefix: %prefix'

	help_description = """**Botmaster(s)**: %authors
**Source Code**: %source
**Need support?**: Join us on [Discord](%discord)!
**Like this bot?**: Support us on [Patreon](%patreon)!
**Invite this bot?**: Click %invite!

**General Commands**
**`help <command>`**: Get help menu for command.
**`config`**: Configure server settings such as bot prefix.
**`register`**: Register your ally code.
**`gregister`**: Register your guild mates (**NEW**).
**`invite`**: Invite this bot to your server.

**Channel Commands**
**`news`**: Keep track of official news from the game developers.
**`payout`**: Keep track of time left to payout for your shard members in arena.

**Guild Commands**
**`gc`**: Guild comparison by roster.
**`gs`**: Guild comparison by stats.
**`glist`**: List guild members by unit GP, gear, level, rarity.

**Player Commands**
**`arena`**: Show arena squad details.
**`gac`**: Compare GAC statistics of different players (**NEW**).
**`gear`**: List equipment needed for characters.
**`gear13`**: List most popular gear 13 characters you don't have.
**`kit`**: List skills of a given unit and their descriptions (**NEW**).
**`locked`**: Show locked characters or ships.
**`mc`**: Show characters with missing mods or having weak mods.
**`meta`**: Show information about best arena and fleet squads.
**`needed`**: Show information about needed modsets globally.
**`pc`**: Player comparison by roster.
**`ps`**: Player comparison by stats.
**`recos`**: Show information about recommended mods.
**`relic`**: List most popular characters relic.
**`wntm`**: List characters who needs mods with specific criteria.
**`zetas`**: List most popular zetas you don't have."""
#NOT WORKING **`mods`**: Show information about mods.
#NOT WORKING **`stats`**: Show statistics about equipped mods."""

	def format_tokens(self, text):

		for token in self.tokens:

			value = token in self.config and self.config[token] or ''
			if token == 'source':
				value = '[Github](%s)' % value

			elif token == 'invite':
				value = self.bot.get_invite_link(invite_msg='HERE')

			if type(value) is list:
				value = ', '.join(value)

			text = text.replace('%' + token, value)

		return text

	async def general_help(self, ctx):

		help_title = self.format_tokens(self.help_title)
		help_description = self.format_tokens(self.help_description)

		await self.bot.send_embed(ctx, [{
			'title': help_title,
			'description': help_description,
		}])

	@commands.command()
	async def help(self, ctx, command: str = None):

		if command is None:
			return await self.general_help(ctx)

		cmd = self.bot.get_command(command)
		if not cmd:
			print('command not found')
			return self.errors.no_such_command(command)

		if cmd.cog:
			help_title = cmd.cog.help_title
			help_description = cmd.cog.help_description

		elif cmd.parent:
			help_title = cmd.parent.help_title
			help_description = cmd.parent.help_description

		help_title = self.format_tokens(help_title)
		help_description = self.format_tokens(help_description)

		await self.bot.send_embed(ctx, [{
			'title': help_title,
			'description': help_description,
		}])
