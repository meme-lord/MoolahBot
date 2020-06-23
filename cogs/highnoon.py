import asyncio
import json
import logging
import random
import threading
from io import BytesIO
from os import listdir
from os.path import isfile, join
from timeit import default_timer as timer

import discord
from PIL import Image, ImageDraw
from PIL import ImageFont
from discord import File
from discord.ext import commands

from lib import database
from lib.events import EventV2

log = logging.getLogger(__name__)


class HighNoon(commands.Cog):
	"""
	All Skill no Luck!
	"""

	highnoon_lock = threading.Lock()

	def __init__(self, bot):
		self.bot = bot
		self.bot.events[__name__] = {}
		self.bot.events[__name__]['highnoon'] = EventV2()
		self.path = 'data\english_dictionary'
		self.files = [f'{self.path}\\{f}' for f in listdir(self.path) if isfile(join(self.path, f))]
		self.players_ingame = []

	@commands.command(aliases=['hn'])
	async def highnoon(self, ctx, amount: int, opponent: discord.Member):
		"""
		Highnoon is old fashioned cowboy standoff game, where each player is given a random word
		and the fastest shooter to type it in wins the duel

		Usage !highnoon <amount> <opponent>
		shortcut : hn e.g .hn <amount> <opponent>
		"""

		if ctx.author.id in self.players_ingame:
			await ctx.send('You are already in a game!')
			return
		elif opponent.id in self.players_ingame:
			await ctx.send(f'{opponent.display_name} is already in a game!')
			return

		log.info(f"Highnoon ({amount}, {opponent}) initiated by {ctx.author}")
		amount = abs(int(amount))

		try:
			self.players_ingame.append(ctx.author.id)
			self.players_ingame.append(opponent.id)

			with self.highnoon_lock:
				# take moolah from each users balance until highnoon is complete
				# the transaction function already checks if they have sufficient balance
				success, err_msg = database.execute_transaction(8, 0, ctx.author.id, ctx.guild.id, amount)
				if not success:
					await ctx.send(err_msg.format(sender=ctx.author.mention))
					return
				success, err_msg = database.execute_transaction(8, 0, opponent.id, ctx.guild.id, amount)
				if not success:
					await ctx.send(err_msg.format(sender=opponent.mention))
					# roll back the other transaction
					database.execute_transaction(10, ctx.author.id, 0, ctx.guild.id, amount)
					return

			await ctx.send(
				f"A highnoon has started for {amount} moolah between {ctx.author.mention} and {opponent.mention}. {opponent.mention} type yes to start.")
			try:
				msg = await self.bot.wait_for('message',
											  check=(lambda x: x.author.id is opponent.id and x.channel is ctx.channel),
											  timeout=20)
			except asyncio.TimeoutError:
				await ctx.send("Highnoon timed out.")
				# roll back the other transactions
				self.return_moolah(ctx.author.id, opponent.id, ctx.guild.id, amount)
				return

			if msg.content.lower() == 'yes':
				word, image_buffer = self.get_random_word()
				# Send and Close Buffers
				image_buffer.seek(0)
				await ctx.send(file=File(image_buffer, filename=f"{word}.png"))
				image_buffer.close()

				opponent_chk = (lambda x: x.author.id is opponent.id and x.channel is ctx.channel)
				author_chk = (lambda x: x.author.id is ctx.author.id and x.channel is ctx.channel)
				results = await asyncio.gather(self.wait_for_message(opponent_chk, 20),
											   self.wait_for_message(author_chk, 20))
				opponent_msg = results[0][0]
				opponent_time = results[0][1]
				author_msg = results[1][0]
				author_time = results[1][1]

				if opponent_time is None and author_time is None:
					await ctx.send('Timed out')
					self.return_moolah(ctx.author.id, opponent.id, ctx.guild.id, amount)
				elif opponent_time is None and author_time is not None:
					if author_msg.content == word:
						await self.send_win_msg(ctx, ctx.author, opponent, amount, round(author_time, 3), 'too long.')
					else:
						await ctx.send(
							f"{ctx.author.display_name} entered incorrectly and {opponent.display_name} timed out")
						self.return_moolah(ctx.author.id, opponent.id, ctx.guild.id, amount)
				elif opponent_time is not None and author_time is None:
					if opponent_msg.content == word:
						await self.send_win_msg(ctx, opponent, ctx.author, amount, round(opponent_time, 3), 'too long.')
					else:
						await ctx.send(
							f"{opponent.display_name} entered incorrectly and {ctx.author.display_name} timed out")
						self.return_moolah(ctx.author.id, opponent.id, ctx.guild.id, amount)
				elif opponent_msg.content == word or author_msg.content == word:
					if opponent_msg.content == word and opponent_time < author_time:
						winner = opponent
						loser = ctx.author
						winner_time = round(opponent_time, 3)
						loser_time = round(author_time, 3)
						await self.send_win_msg(ctx, winner, loser, amount, winner_time, loser_time)
					elif author_msg.content == word and author_time < opponent_time:
						winner = ctx.author
						loser = opponent
						winner_time = round(author_time, 3)
						loser_time = round(opponent_time, 3)
						await self.send_win_msg(ctx, winner, loser, amount, winner_time, loser_time)

				else:
					await ctx.send("Both Players entered the word wrong!.")
					self.return_moolah(ctx.author.id, opponent.id, ctx.guild.id, amount)

			else:
				await ctx.send("Invalid choice")
				self.return_moolah(ctx.author.id, opponent.id, ctx.guild.id, amount)
		finally:
			self.players_ingame.remove(ctx.author.id)
			self.players_ingame.remove(opponent.id)

	async def wait_for_message(self, check, timeout):
		"""
		Waits for discord message and returns the time taken
		"""
		start = timer()

		try:
			message = await self.bot.wait_for('message',
											  check=check,
											  timeout=timeout)
		except asyncio.TimeoutError:
			return None, None
		end = timer()
		time = (end - start)
		return message, time

	def get_random_word(self):
		"""
		Gets a random word from dictionary and returns the word and its image representation.
		"""
		W, H = 1200, 800
		mainfnt_size = 48

		# Buffers for storing images in memory
		buffer_1 = BytesIO()

		word_file = random.choice(self.files)
		with open(word_file, 'r', encoding='UTF-8') as fp:
			data = json.load(fp)

		colours = ['white', "lightblue", 'lightgreen', 'lightcoral', 'mistyrose', 'lightsalmon', 'khaki']
		word = random.choice(list(data.keys()))
		bg_colour = random.choice(colours)

		im = Image.new("RGBA", (W, H), bg_colour)
		draw = ImageDraw.Draw(im)
		font = ImageFont.truetype("data/fonts/OpenSans-Regular.ttf", mainfnt_size)
		font2 = ImageFont.truetype("data/fonts/OpenSans-Regular.ttf", int(mainfnt_size / 2))
		word_text = f'{word[0].upper()}{word[1:]}'
		w, h = font.getsize(word_text)
		draw.text(((W - w) / 2, (H - h) / 2), word_text, fill="black", font=font)

		# Meaning
		hv = 1.8
		for meaning in data[word]['meanings']:
			meaning = f'{meaning["def"][0].upper()}{meaning["def"][1:]}'
			w2, h2 = font2.getsize(meaning)
			draw.text(((W - w2) / 2, (H - h2) / hv), meaning, fill="black", font=font2)
			hv -= 0.15

		im.save(buffer_1, format='png')
		return word_text, buffer_1

	def return_moolah(self, author_id, opponent_id, guild_id, amount):
		database.execute_transaction(10, author_id, 0, guild_id, amount)
		database.execute_transaction(10, opponent_id, 0, guild_id, amount)

	async def send_win_msg(self, ctx, winner, loser, amount, winner_time, loser_time):
		await ctx.send(
			f"{winner.mention} has won {amount}!.\n{winner.display_name} took {winner_time} while {loser.display_name} took {loser_time}")
		success, err_msg = database.execute_transaction(9, winner.id, 0, ctx.guild.id, amount * 2)
		if not success:
			await ctx.send(err_msg.format(sender='0'))
		on_highnoon_end = self.bot.events[__name__]['highnoon']
		await on_highnoon_end.set(
			{'winner': winner.id, 'loser': loser.id, 'guild': ctx.guild.id, 'amount': amount})


def setup(bot):
	bot.add_cog(HighNoon(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.events.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
