import asyncio
import logging

from discord.ext import commands

from database import get_leaderboard
from lib.events import on_voice_moolah

log = logging.getLogger(__name__)


class Achievements(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.bot.events[__name__] = {}
		asyncio.create_task(self.check_pos_leaderboard())

	@on_voice_moolah
	async def check_pos_leaderboard(self, id):
		# TODO get 1st on the topdog leaderboard
		if int(get_leaderboard(id)) == 1:
			user = self.bot.get_user(int(id))
			channel = await user.create_dm()
			await channel.send('Congrats you are the Topdog')

		elif int(get_leaderboard(id)) <= 10:
			# TODO enter top 10
			user = self.bot.get_user(int(id))
			channel = await user.create_dm()
			await channel.send('Congrats you are in the top ten!')

		elif int(get_leaderboard(id)) <= 100:
			# TODO enter top 100
			user = self.bot.get_user(int(id))
			channel = await user.create_dm()
			await channel.send('Congrats you are in the top hundred!')

	async def hr_vc(self):
		# TODO 100hrs in VC
		pass

	async def cointoss(self):
		# TODO win 100 cointosses
		# TODO Unlucky - lose cointoss 10 times in a row
		pass

	async def ppl_in_vc(self):
		# TODO be in vc with 10 people
		# TODO be in vc with 20 people
		pass

	async def get_promoted(self):
		# TODO promotion - get a different discord role
		pass

	async def slots(self):
		# TODO Gambling Addict - play slots more than 100 times
		pass

	async def gambling(self):
		# TODO gambling problems - lose 100k moolah on gambling
		pass


def setup(bot):
	bot.add_cog(Achievements(bot))
	log.info(__name__ + " loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.event.pop(__name__, None)
	log.info(__name__ + " unloaded!")
