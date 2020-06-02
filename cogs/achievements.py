import asyncio
import logging

from discord.ext import commands

from database import get_achievements_types, has_achievement, get_vctime, set_achievement, get_slot_count
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

	@on_vc_moolah_update
	async def check_pos_leaderboard(self, var):
		# TODO finish this after get_leaderboard is fixed.
		'''
		if var is None:
			log.error(f"check_pos_leaderboard was called with None var")
			return
		log.debug(var)
		for user in var:
			position, _ = get_leaderboard_position(user[0], user[1])
			await self.send_tg_achievement_msg(position, user[0], user[1])'''
		pass

	@on_vc_moolah_update
	async def hr_vc(self, var):
		if var is None:
			return
		for user in var:
			time_m = get_vctime(user[0], user[1])
			if int(time_m) == 6000 and not has_achievement(user[0], user[1], 4):  # 6000 mins is 100hrs
				await set_achievement(user[0], user[1], 4)
				user = self.bot.get_user(user[0])
				channel = await user.create_dm()
				await channel.send(f'Achievement Unlocked: Bubbly, Reach 100hrs in Voice Chat')

	@commands.Cog.listener(name='on_voice_state_update')
	async def on_voice_state_update(self, member, before, after):
		if after.channel is not None:
			ppl_in_channel = len(after.channel.members)
			if ppl_in_channel == 10:
				if not has_achievement(member.id, member.guild.id, 5):
					await set_achievement(member.id, member.guild.id, 5)
					message = "Achievement Unlocked: Is it just me or its hot in here ?, Be in voice chat with 10 people."
					await send_dm(self.bot, member.id, message)
			elif ppl_in_channel == 20 and not has_achievement(member.id, member.guild.id, 6):
				await set_achievement(member.id, member.guild.id, 6)
				message = "Achievement Unlocked: Riot!, Be in voice chat with 20 people."
				await send_dm(self.bot, member.id, message)

	@on_cointoss_end
	async def on_cointoss(self, var):
		if var is None:
			return
		# TODO win 100 cointosses
		# TODO Unlucky - lose cointoss 10 times in a row
		pass

	@commands.Cog.listener(name='on_member_update')
	async def on_member_update(self, before, after):
		if before.roles[-1] != after.roles[-1] and after.roles[-1] > before.roles[-1]:
			if not has_achievement(after.id, after.guild.id, 12):
				await set_achievement(after.id, after.guild.id, 12)
				message = "Achievement Unlocked: Promoted!, Get a different discord role."
				await send_dm(self.bot, after.id, message)

	@on_slots_end
	async def on_slots(self, var):
		if var is None:
			return
		amount = get_slot_count(var[0], var[1])
		if len(amount) >= 100 and not has_achievement(var[0], var[1], 10):
			await set_achievement(var[0], var[1], 10)
			message = "Achievement Unlocked: Gambling Addict!, Play slots more than 100 times."
			await send_dm(self.bot, var[0], message)

	async def gambling(self):
		# TODO gambling problems - lose 100k moolah on gambling
		pass

	async def send_tg_achievement_msg(self, pos, user_id, guild_id):
		if pos == 1 and not has_achievement(user_id, guild_id, 1):  # topdog 1
			user = self.bot.get_user(user_id)
			channel = await user.create_dm()
			await channel.send('Congrats!, you are No.1 in Topdog!')
		elif pos <= 10 and not has_achievement(user_id, guild_id, 2):  # topdog 10
			user = self.bot.get_user(user_id)
			channel = await user.create_dm()
			await channel.send('Congrats!, you are No.10 in Topdog!')
		elif pos <= 100 and not has_achievement(user_id, guild_id, 3):  # topdog 100
			user = self.bot.get_user(user_id)
			channel = await user.create_dm()
			await channel.send('Congrats!, you are No.100 in Topdog!')


def setup(bot):
	# bot.add_cog(Achievements(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.event.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
