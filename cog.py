from discord.ext import commands

class Cog(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.client = bot.client
		self.config = bot.config
		self.errors = bot.errors
		self.logger = bot.logger
		self.options = bot.options
		self.redis = bot.redis
