from discord.ext import commands
import asyncio
import logging
import database
import config
from prettytable import PrettyTable

log = logging.getLogger(__name__)


class Moolah(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.provision = self.bot.loop.create_task(self.moolah_loop())

	@commands.command()
	async def topdog(self, ctx):
		entries = database.topdog()
		x = PrettyTable(["Position", "Name", "Moolah"])
		position = 1
		for entry in entries:
			x.add_row([position, ctx.guild.fetch_member(entry[0]).nick, entry[1]])
		await ctx.send(f"```{x}```")

	async def moolah_loop(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			ids = set()
			for guild in self.bot.guilds:
				for channel in guild.voice_channels:
					real_p = (x for x in channel.members if x.bot is False)
					bots = (x for x in channel.members if x.bot is True)

					if real_p>1:
						for id in real_p:
							ids.add(id)
			database.vc_moolah_earned(ids, config.VC_Moolah)
			await asyncio.sleep(60)
