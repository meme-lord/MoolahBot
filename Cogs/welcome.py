import os
import random

from discord import Embed


class Greetings:
    def __init__(self, bot):
        self.bot = bot
        self.description = "Displays Welcome Memes"
        self.loc = "data/welcome_imgs/"

    async def on_member_join(self, member):
        """
        When a user joins a server, this hook gets a random
        welcome message from a folder and uploads it to the default channel.
        :param member:
        :return:
        """
        image = random.choice([self.loc + x for x in os.listdir(self.loc)])
        with open(image, 'r') as fp:
            embed = Embed(title="                ",
                          description="Welcome to our humble abode :island:  " + member.mention, color=0xf1ec1b)
            await self.bot.send_message(member.server.default_channel, embed=embed, file=image)


def setup(bot):
    bot.add_cog(Greetings(bot))
