import logging
from datetime import timedelta
from io import BytesIO
from math import radians

import matplotlib
import matplotlib.ticker as ticker
from PIL import Image, ImageDraw, ImageFont
from discord import File, Member
from discord.ext import commands
from matplotlib import pyplot as plt
from matplotlib.pyplot import text

from lib.database import get_user_balance, get_property, get_vctime, get_leaderboard_position, get_moolah_history, \
	get_achievements

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
	async def profile(self, ctx, person: Member = None):
		"""
		Shows you all your stats
		"""
		if person is None:
			person = ctx.author
		# Img dimensions
		W, H = (600, 600)

		# Buffers for storing images in memory
		buffer_1 = BytesIO()
		buffer_2 = BytesIO()
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
			pos, _ = get_leaderboard_position(person.id, ctx.guild.id)
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
			graph = m_balance_graph(person.id, ctx.guild.id)
			graph.savefig(buffer_1)  # , transparent=True)
			graph.close()

			# Create Achievement progress bar
			if 'Achievements' in self.bot.cogs:
				total_ach = len(self.bot.cogs['Achievements'].achievement_types)
				achievements = len(get_achievements(person.id, ctx.guild.id))
				graph2 = circle_progress(achievements, total_ach)
				graph2.savefig(buffer_2)  # , transparent=True)
				graph2.close()

				buffer_2.seek(0)
				graph2 = Image.open(buffer_2)
				img.paste(graph2, (0, 258))

			buffer_1.seek(0)
			graph = Image.open(buffer_1)
			img.paste(graph, (-45, 390))

			# Paste Profile Pic
			profpic = await get_profile_pic(person)
			img.paste(profpic, (240, 50))
			buffer_1.seek(0)
			img.save(buffer_1, format='png')

			# Send and Close Buffers
			buffer_1.seek(0)
			await ctx.send(file=File(buffer_1, filename=f"{person.id}.png"))
		finally:
			buffer_1.close()


async def get_profile_pic(person):
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


@ticker.FuncFormatter
def clean_formatter(x, pos):
	return clean_money(x)


def m_balance_graph(user_id: int, guild_id: int):
	"""
	Creates a linegraph for moolah balance over a time period.
	"""
	plt.style.use(['dark_background'])
	matplotlib.rcParams['axes.facecolor'] = 'black'
	matplotlib.rc('figure', figsize=(7, 2.1), facecolor='b')
	matplotlib.rcParams.update({'font.size': 6})
	fig, ax = plt.subplots()

	x_axis_time, y_axis_moolah = get_moolah_history(user_id, guild_id)
	ax.fill_between(x_axis_time, y_axis_moolah, color="skyblue", alpha=0.3)
	ax.set_xticklabels([])
	ax.yaxis.set_major_formatter(clean_formatter)
	ax.tick_params(
		axis='x',  # changes apply to the x-axis
		which='both',  # both major and minor ticks are affected
		bottom=False,  # ticks along the bottom edge are off
		top=False,  # ticks along the top edge are off
		labelbottom=False)
	ax.set_xlabel('Moolah vs Time              ', fontsize='medium')
	return plt


def circle_progress(no: int, max):
	# plt.style.use(['dark_background'])
	matplotlib.rc('figure', figsize=(1.5, 1.5), facecolor='b')
	fig, _ = plt.subplots()
	ax = plt.subplot(projection='polar')
	r_v = [radians(no / max * 360), 0]
	ax.barh([1, 0], r_v, color='#FFFF00')
	# Turn off tick labels
	ax.set_yticklabels([])
	ax.set_xticklabels([])
	# Hide grid lines
	ax.grid(False)
	ax.axis('off')
	text(0.5, 0.5, f'Achievements\n{no}/{max}', horizontalalignment='center', verticalalignment='center',
		 transform=ax.transAxes)
	return plt


def setup(bot):
	bot.add_cog(PersonalStats(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.events.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
