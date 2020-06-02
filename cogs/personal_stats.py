import logging
import random
from datetime import timedelta, datetime
from io import BytesIO

import matplotlib
from PIL import Image, ImageDraw, ImageFont
import discord
from discord import File
from discord.ext import commands
from matplotlib import pyplot as plt

from database import get_user_balance, get_property, get_vctime, get_leaderboard_position

log = logging.getLogger(__name__)


class PersonalStats(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.bot.events[__name__] = {}
		self.black = 'data/personal_stats/black.png'
		# Load Fonts
		self.fnt = ImageFont.truetype('data//fonts//Cuadra-Bold.otf', 70)
		self.fnt2 = ImageFont.truetype('data//fonts//Cuadra-Bold.otf', 20)

	@commands.command()
	async def profile(self, ctx, person: discord.Member = None):
		if person is None:
			person = ctx.author
		# Img dimensions
		W, H = (600, 600)

		# Buffers for storing images in memory
		bytIO2 = BytesIO()
		# Load Background Image and create draw object
		try:
			with open(self.black, 'rb') as f:
				img = Image.open(BytesIO(f.read()))
			draw = ImageDraw.Draw(img)

			# Moolah Text
			moolahtxt = clean_money(get_user_balance(person.id, ctx.guild.id))
			w, h = draw.textsize(moolahtxt, font=self.fnt)
			draw.text(((W - w) / 2, (H - h) / 1.8), moolahtxt, font=self.fnt, fill=(255, 255, 0))

			# VC TIME
			vctime = str(timedelta(minutes=get_vctime(person.id, ctx.guild.id)))
			w1, h1 = draw.textsize(vctime, font=self.fnt2)
			draw.text(((W - w1) / 10.5, (H - h1) / 7.5), vctime[:-3], font=self.fnt2, fill=(255, 255, 0))

			# Username Text
			usrtxt = str(person.name)
			w, h = draw.textsize(usrtxt, font=self.fnt2)
			draw.text(((W - w) / 2, (H - h) / 2.6), usrtxt, font=self.fnt2, fill=(255, 255, 0))

			# LeaderBoard Position
			pos,_ = get_leaderboard_position(person.id, ctx.guild.id)
			msg_sent = str(pos)
			w1, h1 = draw.textsize(msg_sent, font=self.fnt2)
			draw.text((int((W - w1) / 1.1), (H - h1) / 7.5), msg_sent, font=self.fnt2, fill=(255, 255, 0))

			# Lifetime Moolah
			lt_moolah = clean_money(get_property("lifetime_moolah", person.id, ctx.guild.id))
			w1, h1 = draw.textsize(lt_moolah, font=self.fnt2)
			draw.text(((W - w1) / 10.5, (H - h1) / 2.9), lt_moolah, font=self.fnt2, fill=(255, 255, 0))

			# Use Discord Default
			jtime = str(person.joined_at.strftime("%d-%b-%y  %I:%M"))
			w1, h1 = draw.textsize(jtime, font=self.fnt2)
			draw.text(((W - w1) / 1.06, (H - h1) / 2.9), jtime, font=self.fnt2, fill=(255, 255, 0))

			# Create Moolah Graph
			graph = m_balance_graph()
			graph.savefig(bytIO2)
			bytIO2.seek(0)
			graph = Image.open(bytIO2)

			img.paste(graph, (-45, 390))

			# Paste Profile Pic
			profpic = await self.get_profile_pic(person)
			img.paste(profpic, (240, 50))
			bytIO2.seek(0)
			img.save(bytIO2, format='png')

			# Send and Close Buffers
			bytIO2.seek(0)
			await ctx.send(file=File(bytIO2, filename=f"{person.id}.png"))
		except Exception as e:
			log.error(e)
		finally:
			bytIO2.close()

	async def get_profile_pic(self, person):
		"""
		Downloads Discord profile pic and loads it
		:returns ImageObj , buffer:
		"""
		f = BytesIO(await person.avatar_url_as(size=128, format='png').read())
		profpic = Image.open(f)
		return profpic


def clean_money(amount):
	"""
	Takes large numbers and converts them into a presentable format.
	ie. 1999 == 1.9k
	:param amount:
	:returns str(amount):
	"""
	amount = abs(int(amount))
	for divider in [(1E+18, ' T'), (1E+9, ' B'), (1E+6, ' M'), (1E+3, ' K')]:
		if amount >= divider[0]:
			num = str(amount / divider[0])
			i = num.index(".")
			truncated = num[:i + 3]
			return truncated + divider[1]
		elif amount < 1E+3:
			return str(amount)


def m_balance_graph():
	"""
	Creates a linegraph for moolah balance over a time period.
	"""
	plt.style.use(['dark_background'])
	matplotlib.rcParams['axes.facecolor'] = 'black'
	matplotlib.rc('figure', figsize=(7, 2), facecolor='b')
	fig, ax = plt.subplots()
	ax.fill_between(range(10), [random.randint(1, 100) for x in range(10)], color="skyblue", alpha=0.3)
	return plt


def setup(bot):
	bot.add_cog(PersonalStats(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.event.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
