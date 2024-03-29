import asyncio
import logging
import secrets

import discord
from discord.ext import commands

from lib import database
from lib.events import EventV2

log = logging.getLogger(__name__)


class CoinToss(commands.Cog):
	"""
	Letting you lose all your Moolah since 2017!
	"""

	cointoss_lock = asyncio.Lock()

	def __init__(self, bot):
		self.bot = bot
		self.bot.events[__name__] = {}
		self.bot.events[__name__]['cointoss'] = EventV2()
		self.outcomes = ['heads', 'tails']  # could have other sets of outcomes? roulette anyone?
		self.players_ingame = []

	@commands.command(aliases=['coinflip'])
	async def cointoss(self, ctx, amount: int, opponent: discord.Member):
		log.info(f"cointoss({amount}, {opponent}) initiated by {ctx.author}")
		amount = abs(int(amount))

		if ctx.author.id in self.players_ingame:
			await ctx.send('You are already in a game!')
			return
		elif opponent.id in self.players_ingame:
			await ctx.send(f'{opponent.display_name} is already in a game!')
			return
		try:
			self.players_ingame.append(ctx.author.id)
			self.players_ingame.append(opponent.id)

			async with self.cointoss_lock:
				# take moolah from each users balance until cointoss is complete
				# the transaction function already checks if they have sufficient balance
				success, err_msg = database.execute_transaction(2, 0, ctx.author.id, ctx.guild.id, amount)
				if not success:
					await ctx.send(err_msg.format(sender=ctx.author.mention))
					return
				success, err_msg = database.execute_transaction(2, 0, opponent.id, ctx.guild.id, amount)
				if not success:
					await ctx.send(err_msg.format(sender=opponent.mention))
					# roll back the other transaction
					database.execute_transaction(7, ctx.author.id, 0, ctx.guild.id, amount)
					return
			await ctx.send(
				f"A cointoss has started for {amount} moolah between {ctx.author.mention} and {opponent.mention}. {opponent.mention} choose your side, heads or tails?")
			try:
				msg = await self.bot.wait_for('message',
											  check=(lambda x: x.author.id is opponent.id and x.channel is ctx.channel),
											  timeout=20)
			except asyncio.TimeoutError:
				await ctx.send("Cointoss timed out.")
				# roll back the other transactions
				database.execute_transaction(7, ctx.author.id, 0, ctx.guild.id, amount)
				database.execute_transaction(7, opponent.id, 0, ctx.guild.id, amount)
				return
			outcome = secrets.choice(self.outcomes)  # we need secure randomness!
			if msg.content.lower() in self.outcomes:
				winner = ctx.author
				loser = opponent
				if msg.content.lower() == outcome:
					winner = opponent
					loser = ctx.author
				await ctx.send(f"The coin landed on {outcome}. {winner.mention} won {amount} Moolah!")
				success, err_msg = database.execute_transaction(3, winner.id, 0, ctx.guild.id, amount * 2)
				if not success:
					await ctx.send(err_msg.format(sender='0'))
				on_cointoss_end = self.bot.events[__name__]['cointoss']
				await on_cointoss_end.set({'winner': winner.id, 'loser': loser.id, 'guild': ctx.guild.id})
			else:
				await ctx.send("Invalid choice")
				database.execute_transaction(7, ctx.author.id, 0, ctx.guild.id, amount)
				database.execute_transaction(7, opponent.id, 0, ctx.guild.id, amount)
		finally:
			self.players_ingame.remove(ctx.author.id)
			self.players_ingame.remove(opponent.id)


def setup(bot):
	bot.add_cog(CoinToss(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.events.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
