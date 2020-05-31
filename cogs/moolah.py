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
		for entry in entries:
			member = await ctx.guild.fetch_member(entry[0])
			x.add_row([position, member.display_name, entry[1]])
			position += 1
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
			# award the vc moolah
			ids = set()
			for guild in self.bot.guilds:
				for channel in guild.voice_channels:
					real_p = [x for x in channel.members if x.bot is False]
					if len(real_p) > 1:
						for discord_id in real_p:
							ids.add((discord_id, guild.id))
							await onup.set([discord_id])
			database.vc_moolah_earned(ids, config.vc_moolah)
			# clean up message dict
			five_mins_ago = datetime.datetime.now(datetime.timezone.utc) - self.time_between_moolah_msgs
			# this dict loop runs every minute maybe impact can be reduced?
			for key, value in self.recent_msg_tracking:
				if (value - five_mins_ago) > self.time_between_moolah_msgs:
					self.recent_msg_tracking.pop(key, None)
			await asyncio.sleep(config.vc_time)


def setup(bot):
	bot.add_cog(Moolah(bot))
	log.info(__name__ + " loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.event.pop(__name__, None)
	log.info(__name__ + " unloaded!")
