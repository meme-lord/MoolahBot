import logging
import os
import random

from discord import Embed
from discord import File
from discord.ext import commands

log = logging.getLogger(__name__)


class Welcome(commands.Cog):
	"""Displays Welcome Memes"""

	def __init__(self, bot):
		self.bot = bot
		self.loc = "data/welcome_imgs/"
		self.bot.events[__name__] = {}

	@commands.Cog.listener(name='on_member_join')
	async def on_member_join(self, member):
		"""
		When a user joins a server, this hook gets a random
		welcome message from a folder and uploads it to the default channel.
		:param member:
		:return:
		"""
		image = random.choice([self.loc + x for x in os.listdir(self.loc)])
		embed = Embed(title="                ",
					  description="Welcome to our humble abode :island:  " + member.mention, color=0xf1ec1b)
		await member.guild.system_channel.send(embed=embed, file=File(image))


async def setup(bot):
	await bot.add_cog(Welcome(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.events.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
