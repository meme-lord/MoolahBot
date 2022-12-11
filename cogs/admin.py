import logging
import subprocess
import sys

from discord.ext import commands

from lib.utils import is_bot_admin, emb

log = logging.getLogger(__name__)


class Admin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.bot.events[__name__] = {}

	@commands.command(pass_context=True)
	@is_bot_admin()
	async def load(self, ctx, extension_name: str):
		"""
		Loads an extension.
		"""
		try:
			self.bot.load_extension(f'cogs.{extension_name}')
			await ctx.message.channel.send(emb("Module [{}] Loaded".format(extension_name)))
		except (AttributeError, ImportError) as e:
			await ctx.message.channel.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))

	@commands.command(pass_context=True)
	@is_bot_admin()
	async def unload(self, ctx, extension_name: str):
		"""
		Unloads an extension.
		"""
		try:
			self.bot.unload_extension(f'cogs.{extension_name}')
			await ctx.message.channel.send(emb("Module [{}] Unloaded!.".format(extension_name)))
		except (AttributeError, ImportError) as e:
			await ctx.message.channel.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))

	@commands.command(pass_context=True)
	@is_bot_admin()
	async def reload(self, ctx, extension_name: str):
		"""
		Reloads an extension.
		"""
		self.bot.reload_extension(f'cogs.{extension_name.lower()}')
		await ctx.send(emb(f'{extension_name.lower()} reloaded!'))

	@commands.command(pass_context=True)
	@is_bot_admin()
	async def update(self, ctx):
		"""
		Git Pulls and updates the bot code
		"""
		log.info(emb(f'Git pull called, Caller:[{ctx.author.id}][{ctx.author.name}]'))
		bash_cmd = "git pull"
		process = subprocess.Popen(bash_cmd.split(), stdout=subprocess.PIPE)
		output, error = process.communicate()
		output = output.decode("utf-8")
		log.info(output)
		await ctx.send(emb(output))

		if error is not None:
			log.error(error)

	@commands.command(pass_context=True)
	@is_bot_admin()
	async def shutdown(self, ctx):
		"""
		Initiates a shutdown and unloads all cogs and stops the loop
		"""
		log.warning(f'[{ctx.author.id}][{ctx.author.name}] has initiated a shutdown!')
		self.bot.loop.stop()

	@commands.command(pass_context=True)
	@is_bot_admin()
	async def restart(self, ctx):
		"""
		Initiates a restart and unloads all cogs and sys.exit with code 42
		"""
		log.warning(f'[{ctx.author.id}][{ctx.author.name}] has initiated a shutdown!')
		sys.exit(42)

async def setup(bot):
	await bot.add_cog(Admin(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading

	# Remove Events
	bot.events.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
