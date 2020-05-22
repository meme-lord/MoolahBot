from discord.ext import commands
import asyncio
import logging
import database
import config
from prettytable import PrettyTable

log = logging.getLogger(__name__)


class Moolah(commands.Cog):
	"""Keeping the Moolah economy going"""
	def __init__(self, bot):
		self.bot = bot
		self.provision = self.bot.loop.create_task(self.moolah_loop())

	@commands.command()
	async def topdog(self, ctx):
		entries = database.topdog(ctx.guild.id)
		x = PrettyTable(["Position", "Name", "Moolah"])
		position = 1
		for entry in entries:
			member = await ctx.guild.fetch_member(entry[0])
			x.add_row([position, member.display_name, entry[1]])
			position += 1
		await ctx.send(f"```{x}```")

	@commands.Cog.listener(name='on_message')
	async def on_message(self, message):
		if message.author == self.bot.user:
			return
		database.moolah_earned(message.author.id, message.guild.id, config.msg_moolah)

	async def moolah_loop(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			ids = set()
			for guild in self.bot.guilds:
				for channel in guild.voice_channels:
					real_p = [x for x in channel.members if x.bot is False]
					if len(real_p) > 1:
						for discord_id in real_p:
							ids.add((discord_id, guild.id))
			database.vc_moolah_earned(ids, config.vc_moolah)
			await asyncio.sleep(config.vc_time)

