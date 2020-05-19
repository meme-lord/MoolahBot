import config
from basic_cog import Basic
from moolah import Moolah

import logging
from sys import stdout
from discord.ext import commands

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

        # create the background task and run it in the background

    async def on_ready(self):
        log.info('Bot started\nLogged in as %s (%s)\n' % (self.user.name, self.user.id))
        for server in self.guilds:
            message = "%s : %s\n" % (server.name, server.id)
            for channel in server.channels:
                message += "\t%s %s\n" % (channel.name, channel.id)
            log.info(message)


bot = MyClient(command_prefix='!')
bot.add_cog(Basic(bot))
bot.add_cog(Moolah(bot))
bot.run(config.bot_token)
