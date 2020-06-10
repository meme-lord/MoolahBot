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
		[self.load_extension("cogs." + f.replace(".py", "")) for f in listdir('cogs') if
		 isfile(join('cogs', f)) and f.replace(".py", "") not in [x.lower() for x in self.cogs]]

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
