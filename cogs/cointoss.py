import discord
import database
import threading
import logging
import secrets
import asyncio
from discord.ext import commands

log = logging.getLogger(__name__)


class CoinToss(commands.Cog):
	cointoss_lock = threading.Lock()
	"""Letting you lose all your Moolah since 2017!"""
	def __init__(self, bot):
		self.bot = bot
		self.outcomes = ['heads', 'tails']  # could have other sets of outcomes? roulette anyone?

	@commands.command()
	async def cointoss(self, ctx, amount: int, opponent: discord.Member):
		log.debug(f"cointoss({amount}, {opponent})")
		amount = abs(int(amount))

		with self.cointoss_lock:
			# check that user balance of both players is sufficient
			if database.get_user_balance(ctx.author.id, ctx.guild.id) < amount:
				await ctx.send(f"{ctx.author.mention} does not have enough Moolah!")
				return
			if database.get_user_balance(opponent.id, ctx.guild.id) < amount:
				await ctx.send(f"{opponent.mention} does not have enough Moolah!")
				return
			# take moolah from each users balance until cointoss is complete
			success, err_msg = database.execute_transaction(2, 0, ctx.author.id, ctx.guild.id, amount)
			if not success:
				await ctx.send(err_msg)
				return
			success, err_msg = database.execute_transaction(2, 0, opponent.id, ctx.guild.id, amount)
			if not success:
				await ctx.send(err_msg)
				#roll back the other transaction
				database.execute_transaction(2, ctx.author.id, 0, ctx.guild.id, amount)
				return
		await ctx.send(f"A cointoss has started between {ctx.author.mention} and {opponent.mention}. {opponent.mention} choose your side, heads or tails?")
		try:
			msg = await self.bot.wait_for('message', check=(lambda x: x.author.id is opponent.id and x.channel is ctx.channel), timeout=10)
		except asyncio.TimeoutError:
			await ctx.send("Cointoss timed out.")
			# roll back the other transactions
			database.execute_transaction(2, ctx.author.i, 0, ctx.guild.id, amount)
			database.execute_transaction(2, opponent.id, 0, ctx.guild.id, amount)
		outcome = secrets.choice(self.outcomes)  # we need secure randomness!
		if msg.content.lower() in self.outcomes:
			winner = ctx.author
			if msg.content.lower() is outcome:
				winner = opponent
			await ctx.send(f"{winner.mention} won {amount} Moolah!")
			success, err_msg = database.execute_transaction(2, winner.id, 0, ctx.guild.id, amount*2)
			if not success:
				await ctx.send(err_msg)
		else:
			await ctx.send("Invalid choice")
