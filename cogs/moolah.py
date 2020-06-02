import asyncio
import datetime
import logging

from discord.ext import commands
from prettytable import PrettyTable

import config
import database
from lib.events import EventV2

log = logging.getLogger(__name__)


class Moolah(commands.Cog):
	"""Keeping the Moolah economy going"""
	recent_msg_tracking = dict()

	def __init__(self, bot):
		self.bot = bot
		self.bot.events[__name__] = {}
		self.bot.events[__name__]['moolahVoice'] = EventV2()
		self.provision = self.bot.loop.create_task(self.moolah_loop())
		self.time_between_moolah_msgs = datetime.timedelta(seconds=config.time_between_msg_moolah)

	@commands.command()
	async def topdog(self, ctx):
		entries = database.topdog(ctx.guild.id)
		x = PrettyTable(["Position", "Name", "Moolah"])
		x.align["Name"] = 'l'
		x.align["Moolah"] = 'l'
		position = 1
		author_in_top10 = False
		for discord_id, balance in entries:
			if discord_id == ctx.author.id:
				author_in_top10 = True
			member = await ctx.guild.fetch_member(discord_id)
			x.add_row([position, member.display_name, balance])
			position += 1
		if not author_in_top10:
			x.add_row(['...', '...', '...'])
			position, balance = database.get_leaderboard_position(ctx.author.id, ctx.guild.id)
			x.add_row([position, ctx.author.display_name, balance])
		await ctx.send(f"```{x}```")

	@commands.Cog.listener(name='on_message')
	async def on_message(self, message):
		if message.author == self.bot.user:
			return
		if (message.author.id, message.guild.id) not in self.recent_msg_tracking:
			self.recent_msg_tracking[(message.author.id, message.guild.id)] = message.created_at
			database.moolah_earned(message.author.id, message.guild.id, config.msg_moolah)

	async def moolah_loop(self):
		onup = self.bot.events[__name__]['moolahVoice']
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			log.debug("Start of moolah loop")
			# award the vc moolah
			ids = set()
			for guild in self.bot.guilds:
				for channel in guild.voice_channels:
					real_p = [x for x in channel.members if x.bot is False]
					if len(real_p) > 1:
						for member in real_p:
							ids.add((member.id, guild.id))
			if ids:
				database.vc_moolah_earned(ids, config.vc_moolah)
				await onup.set(list(map(lambda x: x[0], ids)))
			# clean up message dict
			five_mins_ago = datetime.datetime.now() - self.time_between_moolah_msgs
			# this dict loop runs every minute maybe impact can be reduced?
			for key, value in self.recent_msg_tracking.copy().items():
				if value < five_mins_ago:
					self.recent_msg_tracking.pop(key, None)
			await asyncio.sleep(config.vc_time)


def setup(bot):
	bot.add_cog(Moolah(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.event.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
