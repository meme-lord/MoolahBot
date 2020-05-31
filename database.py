import logging
import threading
from typing import List, Set, Tuple

import config
import mydbwrapper

log = logging.getLogger(__name__)
lock = threading.Lock()  # Lock is needed for transaction integrity don't forget to release!


# https://mysqlclient.readthedocs.io/


def execute_transaction(type_id: int, recipient_id: int, sender_id: int, guild_id: int, amount: int):
	log.debug(f"execute_transaction({type_id}, {recipient_id}, {sender_id}, {guild_id}, {amount})")
	# Transactions don't affect lifetime_moolah
	amount = abs(int(amount))
	c = db.cursor()

	with lock:  # A more complex version of this would only lock for the users involved in the transaction
		if sender_id != 0:
			# Get sender balance
			c.execute("SELECT balance FROM users WHERE discord_id=%s AND guild_id=%s", (sender_id, guild_id))
			balance = c.fetchone()
			# Check if sender balance is sufficient
			if balance is None:
				return False, "ERROR: User {sender} does not exist"
			if balance[0] < amount:
				return False, "ERROR: User {sender} has insufficient moolah funds"
		log.debug("about to exec transaction")
		# Execute transaction
		c.execute(
			"INSERT INTO transactions (type, amount, recipient, sender, guild_id, timestamp) VALUES (%s, %s, %s, %s, %s, UNIX_TIMESTAMP())",
			(type_id, amount, recipient_id, sender_id, guild_id))
		c.execute("UPDATE users SET balance=balance-%s WHERE discord_id=%s AND guild_id=%s",
				  (amount, sender_id, guild_id))
		c.execute("UPDATE users SET balance=balance+%s WHERE discord_id=%s AND guild_id=%s",
				  (amount, recipient_id, guild_id))
	log.debug(f"execute_transaction({type_id}, {recipient_id}, {sender_id}, {amount}) -> SUCCESS")
	return True, f"{amount} Moolah sent from {sender_id} to {recipient_id}"


# users is an array of tuples of (userid, guildid) that are in vc
def vc_moolah_earned(users: Set[Tuple[int, int]], amount: int):
	amount = abs(int(amount))
	c = db.cursor()

	with lock:
		c.executemany(
			f"UPDATE users SET balance=balance+{amount},lifetime_moolah=lifetime_moolah+{amount} WHERE discord_id=%s AND guild_id=%s",
			users)
	c.executemany(
		f"INSERT INTO transactions (type, amount, recipient, sender, guild_id, timestamp) VALUES (5, {amount}, %s, 0, %s, UNIX_TIMESTAMP())",
		users)


def moolah_earned(discord_id: int, guild_id: int, amount: int):
	amount = abs(int(amount))
	c = db.cursor()

	with lock:
		c.execute(
			f"UPDATE users SET balance=balance+%s,lifetime_moolah=lifetime_moolah+%s WHERE discord_id=%s AND guild_id=%s",
			(amount, amount, discord_id, guild_id))
	c.execute(
		f"INSERT INTO transactions (type, amount, recipient, sender, guild_id, timestamp) VALUES (%s, %s, %s, 0, %s, UNIX_TIMESTAMP())",
		(4, amount, discord_id, guild_id))


def topdog(guild_id: int):
	c = db.cursor()
	c.execute(
		"SELECT discord_id, balance FROM users WHERE guild_id=%s AND discord_id!=0 ORDER BY balance DESC LIMIT 10",
		(guild_id,))
	return c.fetchall()


def add_user(discord_id: int, guild_id: int):
	global member_dict
	if guild_id not in member_dict:
		member_dict[guild_id] = set()
	if discord_id not in member_dict[guild_id]:
		c = db.cursor()
		c.execute(
			"INSERT INTO users (discord_id, guild_id, balance, lifetime_moolah) VALUES (%s, %s, 0, 0)",
			(discord_id, guild_id))
		member_dict[guild_id] = discord_id


def add_users(discord_ids: List[int], guild_id: int):
	global member_dict
	log.info(f"add_users({discord_ids}, {guild_id})")
	new_users = list()
	if guild_id not in member_dict:
		member_dict[guild_id] = set()
	for discord_id in discord_ids:
		if discord_id not in member_dict[guild_id]:
			new_users.append((discord_id, guild_id))

	c = db.cursor()
	c.executemany(
		"INSERT INTO users (discord_id, guild_id, balance, lifetime_moolah) VALUES (%s, %s, 0, 0)",
		new_users)
	member_dict[guild_id].update(new_users)


# Returns a dict with guild id as key and list of users as value
def get_member_id_dict():
	global member_dict
	if member_dict is None:
		c = db.cursor()
		c.execute("SELECT discord_id, guild_id FROM users")
		results = c.fetchall()
		guild2ids = dict()
		for result in results:
			if result[1] not in guild2ids:
				guild2ids[result[1]] = set()
			guild2ids[result[1]].add(result[0])
		member_dict = guild2ids
	return member_dict


def get_user_balance(discord_id: int, guild_id: int):
	log.debug(f"get_user_balance({discord_id}, {guild_id})")
	c = db.cursor()
	c.execute("SELECT balance FROM users WHERE discord_id=%s and guild_id=%s", (discord_id, guild_id))
	res = c.fetchone()
	if res is None:
		log.error(f"User {discord_id} for guild {guild_id} did not appear in the DB")
		res = (0,)
	log.debug(f"get_user_balance({discord_id}, {guild_id}) is returning {res[0]}")
	return res[0]


def get_property(c_name: str, userid: int, guildid: int):
	c = db.cursor()
	log.debug(f"get_user_{c_name}({userid}, {guildid})")
	c.execute(f"SELECT {c_name} FROM users WHERE discord_id=%s and guild_id=%s", (userid, guildid))
	res = c.fetchone()
	if res is None:
		log.error(f"User {userid} for guild {guildid} did not appear in the DB")
		res = (0,)
	r = res[0]
	log.debug(f"get_user_{c_name}({userid}, {guildid}) is returning {r}")
	c.close()
	return r


def get_vctime(userid: int, guildid: int):
	"""
	Counts the number of voice chat awarded transactions
	"""
	c = db.cursor()
	c.execute("SELECT COUNT(*) FROM transactions WHERE type=5 and recipient=%s and guild_id=%s", (userid, guildid))
	res = c.fetchone()
	if res is None:
		return 0
	return res[0]


def get_leaderboard_position(user_id, guild_id):
	"""
	Gets list of total users and iterates through the list to find user.
	and returns index position +1
	:return int:
	"""
	c = db.cursor()
	c.execute("SELECT discord_id, balance FROM users WHERE guild_id=%s ORDER BY balance DESC", (guild_id,))
	pos = list(filter(lambda x: int(x[0]) == int(user_id), c.fetchall()))
	result = (0, 0)
	if pos:
		pos = pos[0]
		result = (int(pos[0]), int(pos[1]))
	c.close()

	return result


db = mydbwrapper.disconnectSafeConnect(config.DB_HOST, config.DB_USER, config.DB_PASS, config.DB_DATABASE)
# db = MySQLdb.connect()
db.autocommit(True)
member_dict = None
get_member_id_dict()
