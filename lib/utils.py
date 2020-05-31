import asyncio
from difflib import get_close_matches

import discord
from discord.ext import commands
from emoji import UNICODE_EMOJI


class usernotFound(Exception):
	def __init__(self, user, match=None):
		self.muser = user
		self.match = match

	def __str__(self):
		if self.match is None:
			return "User [{}] not found!.".format(self.muser)
		else:
			return "User [{}] not found!.\n Did u mean {} ?.".format(self.muser, self.match)


async def search(ctx, member, type='users'):
	member = str(member).lower()
	memberlist = ctx.guild.members
	name_list = [(str(x.name).lower(), str(x.nick).lower(), x) for x in ctx.guild.members]
	match = get_close_matches(member, [x[0] for x in name_list])
	match2 = get_close_matches(member, [x[1] for x in name_list])
	if len(match) != 0:
		name_user_match = [x[2] for x in name_list if x[0] == match[0]][0]
		return name_user_match
	elif len(match) == 0:
		if len(match2) != 0:
			nick_user_match = [x[2] for x in name_list if x[1] == match2[0]][0]
			return nick_user_match
		elif len(match2) == 0:
			if member.isdigit():
				nameid = discord.utils.get(memberlist, id=int(member))
				return nameid
			elif "@" in member[1:2]:
				user = member.strip('<')
				user = user.strip('>')
				user = user.strip('@')
				user = user.strip('!')
				user = discord.utils.get(ctx.guild.members, id=int(user))
				return user
			else:

				raise usernotFound(member)


def is_admin():
	"""
	Checks if the User has admin permissions
	:return:
	"""

	@asyncio.coroutine
	def predicate(ctx):
		if ctx.author.guild_permissions.administrator:
			return True
		else:
			return False

	return commands.check(predicate)


def emb(item):
	"""
	Return the item in a codeblock format.
	:param item:
	:return:
	"""
	return '```' + str(item) + '```'


def is_emoji(s):
	"""
	Checks if the letter s is an emoji.
	:param s:
	:return:
	"""
	return s in UNICODE_EMOJI


def emoji_norm(txt, emoji):
	"""
	Replace emoji characters with the specified character.
	:param txt:
	:return:
	"""
	red = [x for x in txt]
	ind = []
	for letter, inde in zip(txt, range(0, len(txt))):
		condition = is_emoji(letter)
		if condition:
			ind.append(inde)
	for x in ind:
		red[x] = "_"
	return "".join(red)
