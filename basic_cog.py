from discord.ext import commands


class Basic(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def ping(self, ctx):
		await ctx.send('pong')

	@commands.command()
	async def pong(self, ctx):
		await ctx.send("Don't get smart with me kiddo")
