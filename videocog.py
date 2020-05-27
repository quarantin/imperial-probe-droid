import json
import traceback
from datetime import datetime

from discord.ext import commands, tasks

import cog

import DJANGO
from swgoh.models import Player, PlayerConfig

class VideoCog(cog.Cog):

	max_raid_tickets = 600
	max_guild_tokens = 10000

	def __init__(self, bot):
		super().__init__(bot)
		self.videos_updater.start()

	def cog_unload(self):
		self.videos_updater.cancel()

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):

		if isinstance(error, commands.CommandNotFound):
			return

		raise error

	@tasks.loop(minutes=1)
	async def videos_updater(self, min_tickets: int = 600):

		now = datetime.now()

		alerts = self.get_raid_tickets_config()
		for alert in alerts:

			notif_time = datetime.strptime(alert.value, '%H:%M')
			premium_user = alert.premium_user

			hour_ok = now.hour == notif_time.hour
			minute_ok = now.minute == notif_time.minute
			if hour_ok and minute_ok:

				lines = []
				guild_activity = await self.get_guild_activity(creds_id=premium_user.creds_id, notify=True)
				raid_tickets = guild_activity['raid-tickets']

				for name, tickets in sorted(raid_tickets.items(), key=lambda x: x[1], reverse=True):
					if tickets < min_tickets:
						pad = self.get_lpad_tickets(tickets)
						lines.append('`| %s%d/%d |` __**%s**__' % (pad, tickets, min_tickets, name))

				channel = self.bot.get_channel(alert.channel_id)
				await channel.send('\n'.join(lines))

	@commands.command(aliases=['vids', 'video'])
	async def videos(self, ctx, *, command: str = ''):

		lines = []
		guild_activity = await self.get_guild_activity(creds_id=premium_user.creds_id, notify=notify)
		raid_tickets = guild_activity['raid-tickets']
		for name, tickets in sorted(raid_tickets.items(), key=lambda x: x[1], reverse=True):
			if tickets < min_tickets :
				pad = self.get_lpad_tickets(tickets)
				lines.append('`| %s%d/%d |` __**%s**__' % (pad, tickets, min_tickets, name))

		sep = self.config['separator']
		lines = [ sep ] + lines + [ sep ]

		await ctx.send('\n'.join(lines))
