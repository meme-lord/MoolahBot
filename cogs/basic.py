import logging

from discord.ext import commands

log = logging.getLogger(__name__)


class Basic(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.bot.events[__name__] = {}

	@commands.command()
	async def ping(self, ctx):
		"""
		What do you think?
		"""
		await ctx.send('pong')

	@commands.command(hidden=True)
	async def pong(self, ctx):
		await ctx.send("Don't get smart with me kiddo")


async def setup(bot):
	await bot.add_cog(Basic(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.events.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
