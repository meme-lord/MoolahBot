import logging
from datetime import datetime, timedelta

from discord import AuditLogAction
from discord.ext import commands

from lib.utils import send_dm, emb

log = logging.getLogger(__name__)


class RougeGuard(commands.Cog):
	"""
	Prevents malicious actors from wiping the server by kicking and banning its users.
	"""

	def __init__(self, bot):
		self.bot = bot
		self.bot.events[__name__] = {}
		self.bot.add_listener(self.on_member_remove)

	async def on_member_remove(self, member):
		"""
		Checks if user was kicked or banned and then get the users kick/ban history.
		If the user has kicked or banned more than 3 times in 2 weeks, remove all roles with kick/ban privileges.
		"""
		b_k = await member.guild.audit_logs(limit=None).flatten()
		b_k = [x for x in b_k if x.created_at > (datetime.utcnow() - timedelta(minutes=1))]
		ba = [entry for entry in b_k if entry.target.id == member.id]
		if len(ba) != 0:
			b_k_user = ba[0].user
			bans = await member.guild.audit_logs(user=b_k_user,
												 after=datetime.utcnow() - timedelta(weeks=2),
												 action=AuditLogAction.ban).flatten()
			kicks = await member.guild.audit_logs(user=b_k_user,
												  after=datetime.utcnow() - timedelta(weeks=2),
												  action=AuditLogAction.kick).flatten()
			if len(bans) > 3 or len(kicks) > 3 and not b_k_user.top_role.permissions.administrator:
				if not b_k_user.guild.owner_id == b_k_user.id:
					roles_to_remove = [role for role in b_k_user.roles if
									   role.permissions.ban_members or role.permissions.kick_members]
					await b_k_user.remove_roles(roles_to_remove,
												reason='RougeGuard: User banned/kicked more than 3 times in 2 weeks',
												atomic=True)
					log.info(
						f'RougeGuard Triggered: [{b_k_user.id}] removed\
						more than 3 users from guild [{b_k_user.guild.id}]- Removed users roles')
					message = emb(
						'You have removed more than 3 users, your mod roles are temporarily removed until further investigation')
					await send_dm(self.bot, b_k_user.id, message)


def setup(bot):
	bot.add_cog(RougeGuard(bot))
	log.info(f"{__name__} loaded!")


def teardown(bot):
	# Actions before unloading
	# Remove Events
	bot.events.pop(__name__, None)
	log.info(f"{__name__} unloaded!")
