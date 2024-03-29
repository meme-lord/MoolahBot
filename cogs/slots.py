import asyncio
import logging
import secrets

from discord.ext import commands

from lib import database
from lib.events import EventV2

log = logging.getLogger(__name__)


class Slots(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.bot.events[__name__] = {}
		self.bot.events[__name__]['slots'] = EventV2()

	@commands.command()
	async def slots(self, ctx, amount):
		"""
		The Slot machine, a sure way of getting nothing from something.
		Command: !slots <moolah_amount>
		"""
		log.info(f"slots({amount}) initiated by {ctx.author}")
		try:
			amount = abs(int(amount))
		except ValueError as e:
			log.info(e)
			await ctx.send(f"{amount} is not a valid amount to bet. Must be an integer")

		success, err_msg = database.execute_transaction(6, 0, ctx.author.id, ctx.guild.id, amount)
		if not success:
			await ctx.send(err_msg.format(sender=ctx.author.mention))
			return

		result = []
		items = {"CHERRY": (3, 10, "🍒"),
				 "APPLE": (2, 4, "🍏"),
				 "PLUM": (1.5, 2, "🍑"),
				 "BELL": (1, 1.25, "🚨"),
				 "BOMB": (-0.5, -1, "💣")}
		for _ in range(3):
			result.append(secrets.choice(list(items)))
		slot_machine = '```\n/-----------------------------\\\n| +-------------------------+ |\n| |       SLOT MACHINE      | |  🔴\n| +-------------------------+ |   |\n|    _____________________    |===+\n|   |                     |   |\n|   |   {first}    {second}    {third}   |   |\n|   |_____________________|   |\n|                             |\n| +-------------------------+ |\n\\-----------------------------/\n```'
		sent_msg = await ctx.send(slot_machine.format(first='  ', second='  ', third='  '))

		await sent_msg.edit(content=slot_machine.format(first=items[result[0]][2], second='  ', third='  '))
		await asyncio.sleep(0.6)
		await sent_msg.edit(
			content=slot_machine.format(first=items[result[0]][2], second=items[result[1]][2], third='  '))
		await asyncio.sleep(0.6)
		await sent_msg.edit(content=slot_machine.format(first=items[result[0]][2], second=items[result[1]][2],
														third=items[result[2]][2]))
		won_something = False
		try:
			log.info(f"Result: {result}")
			for item in set(result):
				count = result.count(item)
				if count == 2:
					pool = amount * items[item][0]
					await ctx.send(f"You won {pool} moolah!")
					success, err_msg = database.execute_transaction(6, ctx.author.id, 0, ctx.guild.id, pool)
					if not success:
						await ctx.send(err_msg.format(sender={ctx.author.mention}))
						return
					won_something = True
				elif count == 3:
					pool = amount * items[item][1]
					await ctx.send(f"You won {pool} moolah!")
					recipient = ctx.author.id
					sender = 0
					if pool < 0:
						sender = recipient
						recipient = 0
					success, err_msg = database.execute_transaction(6, recipient, sender, ctx.guild.id, pool)
					if not success:
						await ctx.send(err_msg.format(sender={ctx.author.mention}))
						return
					won_something = True
			if not won_something:
				await ctx.send("Alas luck wasn't on your side")
		finally:
			on_slot_end = self.bot.events[__name__]['slots']
			await on_slot_end.set((ctx.author.id, ctx.guild.id, won_something))


def setup(bot):
	bot.add_cog(Slots(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.events.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
