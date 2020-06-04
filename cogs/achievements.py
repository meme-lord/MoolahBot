import asyncio
import logging

from discord.ext import commands

from database import get_achievements_types, has_achievement, get_vctime, set_achievement, get_slot_count, \
	get_leaderboard_position, get_cointoss_count
from lib.events import on_vc_moolah_update, on_cointoss_end, on_slots_end
from lib.utils import send_dm

log = logging.getLogger(__name__)


class Achievements(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.bot.events[__name__] = {}
		self.achievement_types = get_achievements_types()
		asyncio.create_task(self.check_pos_leaderboard())
		asyncio.create_task(self.hr_vc())
		asyncio.create_task(self.on_cointoss())
		asyncio.create_task(self.on_slots())

	@on_vc_moolah_update
	async def check_pos_leaderboard(self, var):
		if var is None:
			return
		for user in var:
			position, _ = get_leaderboard_position(user[0], user[1])
			await self.send_tg_achievement_msg(position, user[0], user[1])

	@on_vc_moolah_update
	async def hr_vc(self, var):
		if var is None:
			return
		for user in var:
			time_m = get_vctime(user[0], user[1])
			if int(time_m) == 6000:  # 6000 mins is 100hrs
				message = "Achievement Unlocked: Bubbly, Reach 100hrs in Voice Chat"
				await self.give_achievement(user[0], user[1], 4, message)

	@commands.Cog.listener(name='on_voice_state_update')
	async def on_voice_state_update(self, member, before, after):
		if after.channel is not None:
			ppl_in_channel = len(after.channel.members)
			if ppl_in_channel == 10:
				message = "Achievement Unlocked: Is it just me or its hot in here ?, Be in voice chat with 10 people."
				await self.give_achievement(member.id, member.guild.id, 5, message)
			elif ppl_in_channel == 20:
				message = "Achievement Unlocked: Riot!, Be in voice chat with 20 people."
				await self.give_achievement(member.id, member.guild.id, 6, message)

	@on_cointoss_end
	async def on_cointoss(self, var):
		if var is None:
			return
		wins_w = get_cointoss_count(var['winner'], var['guild'], 3)
		total = get_cointoss_count(var['loser'], var['guild'], 2)
		wins = get_cointoss_count(var['loser'], var['guild'], 3)
		refunds = get_cointoss_count(var['loser'], var['guild'], 7)
		loser_losses = (total - refunds) - wins

		if wins_w == 100:
			message = "Achievement Unlocked: 'On a Roll!', 'Win 100 cointosses'"
			await self.give_achievement(var['winner'], var['guild'], 14, message)

		if loser_losses == 100:
			message = "Achievement Unlocked: 'Feels bad man!', 'Lose 100 cointosses'"
			await self.give_achievement(var['loser'], var['guild'], 13, message)

	@commands.Cog.listener(name='on_member_update')
	async def on_member_update(self, before, after):
		if before.roles[-1] != after.roles[-1] and after.roles[-1] > before.roles[-1]:
			message = "Achievement Unlocked: Promoted!, Get a different discord role."
			await self.give_achievement(after.id, after.guild.id, 12, message)

	@on_slots_end
	async def on_slots(self, var):
		if var is None:
			return
		amount = get_slot_count(var[0], var[1])
		if amount >= 100:
			message = "Achievement Unlocked: Gambling Addict!, Play slots more than 100 times."
			await self.give_achievement(var[0], var[1], 10, message)

	async def send_tg_achievement_msg(self, pos, user_id, guild_id):
		if pos == 1:  # topdog 1
			message = "Achievement Unlocked: Topdog, you are No.1 in the leaderboards!"
			await self.give_achievement(user_id, guild_id, 1, message)

		elif pos <= 10:  # topdog 10
			message = "Achievement Unlocked: Welcome to the Champions club!, you are No.10 in the leaderboards!"
			await self.give_achievement(user_id, guild_id, 2, message)

		elif pos <= 100:  # topdog 100
			message = "Achievement Unlocked: Beginnings of a humble Topdog, Reach top 100 in moolah leaderboard."
			await self.give_achievement(user_id, guild_id, 3, message)

	async def give_achievement(self, user_id, guild_id, achievement_id, message):
		if not has_achievement(user_id, guild_id, achievement_id):
			await set_achievement(user_id, guild_id, achievement_id)
			await send_dm(self.bot, user_id, message)


def setup(bot):
	bot.add_cog(Achievements(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.event.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
