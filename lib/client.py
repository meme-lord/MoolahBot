import logging
from os import listdir
from os.path import isfile, join
from sys import stdout

from discord.ext import commands

import config
from lib import database

log = logging.getLogger(__name__)
# noinspection PyArgumentList
logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(message)s",
	handlers=[
		logging.StreamHandler(stdout)
	]
)


class MyClient(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.events = {}

	async def on_ready(self):
		log.info('Bot started\nLogged in as %s (%s)\n' % (self.user.name, self.user.id))

		# Automated Cog Loader
		for f in listdir('cogs'):
			cog_name = f.replace(".py", "")
			if isfile(join('cogs', f)) and cog_name not in map(str.lower, self.cogs):
				self.load_extension(f"cogs.{cog_name}")

		for server in self.guilds:
			message = "%s : %s\n" % (server.name, server.id)
			for channel in server.channels:
				message += "\t%s %s\n" % (channel.name, channel.id)
			log.info(message)
			database.add_user(0, server.id)  # this user is for the bot for temporary transactions
			database.add_users(list(map(lambda x: x.id, list(filter(lambda x: not x.bot, server.members)))), server.id)

	async def on_member_join(self, member):
		database.add_user(member.id, member.guild.id)

	async def on_guild_join(self, guild):
		database.add_users(list(map(lambda x: x.id, list(filter(lambda x: not x.bot, guild.members)))), guild.id)


if __name__ == "__main__":
	bot = MyClient(command_prefix='!')
	bot.run(config.bot_token)
