import asyncio
import json
import logging
import random
import threading
from io import BytesIO
from operator import itemgetter
from os import listdir
from os.path import isfile, join
from timeit import default_timer as timer

from PIL import Image, ImageDraw
from PIL import ImageFont
from discord import File, Embed, Member
from discord.ext import commands

from lib import database
from lib.events import EventV2

log = logging.getLogger(__name__)


def return_moolah(author_id, opponent_id, guild_id, amount):
	database.execute_transaction(10, author_id, 0, guild_id, amount)
	database.execute_transaction(10, opponent_id, 0, guild_id, amount)


class HighNoon(commands.Cog):
	"""
	All Skill no Luck!
	"""

	highnoon_lock = threading.Lock()

	def __init__(self, bot):
		self.bot = bot
		self.bot.events[__name__] = {}
		self.bot.events[__name__]['highnoon'] = EventV2()
		self.path = 'data/english_dictionary'
		self.files = [f'{self.path}\\{f}' for f in listdir(self.path) if isfile(join(self.path, f))]
		self.players_ingame = []
		self.title = "High Noon"

	@commands.command(aliases=['hn'])
	async def highnoon(self, ctx, amount: int, *args: Member):
		"""
		Highnoon is old fashioned cowboy standoff game, where each player is given a random word
		and the fastest shooter to type it in wins the duel

		Usage !highnoon <amount> <opponent> <opponent> etc..
		shortcut : hn e.g .hn <amount> <opponent>
		"""

		if ctx.author.id in self.players_ingame:
			await ctx.send(embed=Embed(title=self.title,
									   description='You are already in a game!', color=0xe0321f))
			return
		elif ctx.author.id in [p.id for p in args]:
			await ctx.send(embed=Embed(title=self.title,
									   description='You cannot play against yourself!', color=0xe0321f))
			return
		cannot_play = [player for player in args if player.id in self.players_ingame or player.bot is True]
		can_play = [player for player in args if player not in cannot_play]
		if len(cannot_play) > 0:
			await ctx.send(embed=Embed(title=self.title,
									   description=f'The following players cannot play as they are in game already:\n{[x.display_name for x in cannot_play]}',
									   color=0xe7cd18))
			if len(can_play) == 0:
				return

		self.players_ingame.append(ctx.author.id)
		self.players_ingame.append([p.id for p in can_play])

		confirm_msg = f'{" ".join([p.mention for p in can_play])} have been challenged to a game of High Noon.\
		 In this game players are given a word and the fastest one to type it in wins.\nType `yes` to continue'
		embed = Embed(title=f"{self.title} Confirmation Message", description=confirm_msg, color=0xe7cd18)
		await ctx.send(embed=embed)
		results = await asyncio.gather(
			*((self.confirmation_check(ctx, p, 'yes', 20)) for p in can_play))
		confirmed_players = [player[0] for player in results if player[1] is True]
		if len(confirmed_players) == 0:
			await ctx.send(embed=Embed(title=self.title,
									   description='Not enough players accepted the game cannot continue.',
									   color=0xe0321f))
			return
		# Add the author to the listen list
		confirmed_players.append(ctx.author)
		await ctx.send(embed=Embed(title=self.title,
								   description=f'{"".join([p.mention for p in confirmed_players])}\n Get ready the game will start soon',
								   color=0xe7cd18))

		try:
			log.info(
				f'{str(ctx.author.id)} has initiated High Noon for {str(amount)} each between {" ".join([str(x.id) for x in confirmed_players])}')
			with self.highnoon_lock:
				# take moolah from each users balance until highnoon is complete
				# the transaction function already checks if they have sufficient balance
				for player in confirmed_players:
					success, err_msg = database.execute_transaction(8, 0, player.id, ctx.guild.id, amount)
					if not success:
						await ctx.send(err_msg.format(sender=player.mention))
						# roll back the other transaction
						database.execute_transaction(10, player.id, 0, ctx.guild.id, amount)
						return

			word_text, buffer = self.get_random_word()
			# Send and Close Buffers
			buffer.seek(0)
			await ctx.send(file=File(buffer, filename=f"{word_text}.png"))
			buffer.close()

			final_results = await asyncio.gather(
				*((self.confirmation_check(ctx, p, word_text, 20)) for p in confirmed_players))
			final_results = [p for p in final_results if p[1] is True]
			if len(final_results) == 0:
				await ctx.send(embed=Embed(title=self.title,
										   description='Everybody got the wrong answer', color=0xe0321f))
				for player in confirmed_players:
					database.execute_transaction(10, player.id, 0, ctx.guild.id, amount)
				return
			final_results.sort(key=itemgetter(2))
			message = f'{final_results[0][0].display_name} is the winner!'
			message += ''.join([f'\n {p[0].display_name} took {round(p[2], 3)} s' for p in final_results])

			embed = Embed(title="Showdown results:", description=message, color=0x00ff40)
			embed.set_thumbnail(url=final_results[0][0].avatar_url)
			await ctx.send(embed=embed)

			success, err_msg = database.execute_transaction(9, final_results[0][0].id, 0, ctx.guild.id,
															amount * len(confirmed_players))
			if not success:
				await ctx.send(err_msg.format(sender='0'))
			on_highnoon_end = self.bot.events[__name__]['highnoon']
			await on_highnoon_end.set(
				{'winner': final_results[0][0].id,
				 'losers': [p for p in confirmed_players if p.id != final_results[0][0].id], 'guild': ctx.guild.id,
				 'amount': amount})
		finally:
			self.players_ingame.remove(ctx.author.id)
			self.players_ingame.remove([p.id for p in can_play])

	def get_random_word(self):
		"""
		Gets a random word from dictionary and returns the word and its image representation.
		"""
		max_w, max_h = 1200, 800
		main_fnt_size = 48

		# Buffers for storing images in memory
		buffer_1 = BytesIO()

		word_file = random.choice(self.files)
		with open(word_file, 'r', encoding='UTF-8') as fp:
			data = json.load(fp)

		colours = ['white', "lightblue", 'lightgreen', 'lightcoral', 'mistyrose', 'lightsalmon', 'khaki']
		word = random.choice(list(data.keys()))
		bg_colour = random.choice(colours)

		im = Image.new("RGBA", (max_w, max_h), bg_colour)
		draw = ImageDraw.Draw(im)
		font = ImageFont.truetype("data/fonts/OpenSans-Regular.ttf", main_fnt_size)
		font2 = ImageFont.truetype("data/fonts/OpenSans-Regular.ttf", int(main_fnt_size / 2))
		word_text = f'{word[0].upper()}{word[1:]}'
		w, h = font.getsize(word_text)
		draw.text(((max_w - w) / 2, (max_h - h) / 2), word_text, fill="black", font=font)

		# Meaning
		hv = 1.8
		for meaning in data[word]['meanings']:
			meaning = f'{meaning["def"][0].upper()}{meaning["def"][1:]}'
			w2, h2 = font2.getsize(meaning)
			draw.text(((max_w - w2) / 2, (max_h - h2) / hv), meaning, fill="black", font=font2)
			hv -= 0.15

		im.save(buffer_1, format='png')
		return word_text, buffer_1

	async def confirmation_check(self, ctx, player, value_chk, timeout):
		start = timer()
		try:
			msg = await self.bot.wait_for('message',
										  check=(
											  lambda x: x.author.id is player.id and x.channel is ctx.channel),
										  timeout=timeout)
		except asyncio.TimeoutError:
			return player, False, 999
		end = timer()
		time = (end - start)
		data = (player, True, time) if msg.content == value_chk else (player, False, time)
		return data


def setup(bot):
	bot.add_cog(HighNoon(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.events.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
