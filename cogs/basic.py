from discord.ext import commands
import logging

log = logging.getLogger(__name__)


class Basic(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def ping(self, ctx):
		await ctx.send('pong')

	@commands.command()
	async def pong(self, ctx):
		await ctx.send("Don't get smart with me kiddo")


def setup(bot):
	bot.add_cog(Basic(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading
	log.info(f"{__name__} unloaded!")
