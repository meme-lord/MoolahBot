import asyncio
import logging

from discord.ext import commands

from database import get_leaderboard_position
from lib.events import on_vc_moolah_update

log = logging.getLogger(__name__)


class Achievements(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.bot.events[__name__] = {}
		asyncio.create_task(self.check_pos_leaderboard())

	@on_vc_moolah_update
	async def check_pos_leaderboard(self, var):
		if var is None:
			log.error(f"check_pos_leaderboard was called with None var")
			return
		log.debug(var)
		for user in var:
			position, _ = int(get_leaderboard_position(user)) #TODO: NEED GUILD ID HERE
			if position in range(1, 100):  # if position in top 100
				user = self.bot.get_user(int(user))
				channel = await user.create_dm()
				await channel.send(f'Congrats!, you are No.{position} in Topdog!')

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
	#bot.add_cog(Achievements(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.event.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
