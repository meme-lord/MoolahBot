import asyncio
import datetime
import logging

from discord.ext import commands
from discord.errors import NotFound
from prettytable import PrettyTable

import config
from lib import database
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

	@commands.command(aliases=['leaderboard'])
	async def topdog(self, ctx):
		"""
		Shows to top 10 leaderboard
		"""
		entries = database.topdog(ctx.guild.id)

		position = 1
		author_in_top10 = False
		entry_list = []
		for discord_id, balance in entries:
			try:
				member = await ctx.guild.fetch_member(discord_id)
			except NotFound:
				continue
			if discord_id == ctx.author.id:
				author_in_top10 = True
			if entry_list and entry_list[-1][2] == balance:
				entry_list.append([entry_list[-1][0], member.display_name, balance])
			else:
				entry_list.append([position, member.display_name, balance])
			if position == 10:
				break
			position += 1
		if not author_in_top10:
			entry_list.append(['...', '...', '...'])
			position, balance = database.get_leaderboard_position(ctx.author.id, ctx.guild.id)
			entry_list.append([position, ctx.author.display_name, balance])

		x = PrettyTable(["Position", "Name", "Moolah"])
		x.align["Name"] = 'l'
		x.align["Moolah"] = 'l'
		for entry in entry_list:
			x.add_row(entry)
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
			ids = self.get_users_in_vc()
			if ids:
				database.vc_moolah_earned(ids, config.vc_moolah)
				await onup.set(list(map(lambda x: x, ids)))
			# clean up message dict
			self.clean_recent_message_dict()
			await asyncio.sleep(config.vc_time)

	def get_users_in_vc(self):
		ids = set()
		for guild in self.bot.guilds:
			for channel in guild.voice_channels:
				real_p = list(filter(eligible_for_moolah, channel.members))
				if len(real_p) > 1:
					for member in real_p:
						ids.add((member.id, guild.id))
		return ids

	def clean_recent_message_dict(self):
		five_mins_ago = datetime.datetime.utcnow() - self.time_between_moolah_msgs
		# this dict loop runs every minute maybe impact can be reduced?
		for key, value in self.recent_msg_tracking.copy().items():
			if value < five_mins_ago:
				self.recent_msg_tracking.pop(key, None)


def eligible_for_moolah(person):
	return person.bot is False and not person.voice.self_deaf and not person.voice.deaf and not person.voice.self_mute and not person.voice.mute


async def setup(bot):
	await bot.add_cog(Moolah(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.events.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
