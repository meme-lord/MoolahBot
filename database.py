import logging
import threading
from datetime import datetime
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
		member_dict[guild_id].add(discord_id)


def add_users(discord_ids: List[int], guild_id: int):
	global member_dict
	log.debug(f"add_users({discord_ids}, {guild_id})")
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
	c.execute("SELECT COUNT(id) FROM transactions WHERE type=5 and recipient=%s and guild_id=%s",
			  (userid, guildid))
	res = c.fetchone()
	if res is None:
		return 0
	return res[0]


def get_slot_count(userid: int, guildid: int):
	"""
	Counts the number of slot transactions
	"""
	c = db.cursor()
	c.execute("SELECT COUNT(id) FROM transactions WHERE type=6 and sender=%s and guild_id=%s", (userid, guildid))
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
	c.execute("SELECT discord_id, balance FROM users WHERE guild_id=%s AND discord_id!=0 ORDER BY balance DESC",
			  (guild_id,))
	user_id = int(user_id)
	people = c.fetchall()
	pos = [x[0] for x in people].index(user_id)
	balance = people[pos][1]
	return pos + 1, balance


def get_achievements(user_id: int, guild_id: int):
	c = db.cursor()
	try:
		c.execute("SELECT * FROM user_achievements WHERE discord_id=%s and guild_id=%s", (user_id, guild_id))
		return c.fetchall()
	finally:
		c.close()


def get_achievements_types():
	data = {}
	c = db.cursor()
	c.execute("SELECT * FROM achievements_types")
	result = c.fetchall()
	for item in result:
		data[item[0]] = {'name': item[1], 'description': item[2]}
	return data


async def set_achievement(user_id: int, guild_id: int, achievement_type: int):
	c = db.cursor()
	c.execute(
		"INSERT INTO user_achievements (discord_id,guild_id, achievement) VALUES (%s, %s, %s)",
		(user_id, guild_id, achievement_type))
	c.close()


def has_achievement(user_id: int, guild_id: int, achievement_type: int):
	c = db.cursor()
	c.execute(
		"SELECT EXISTS(SELECT * FROM user_achievements WHERE discord_id=%s and guild_id=%s and achievement=%s)",
		(user_id, guild_id, achievement_type))
	result = c.fetchone()
	x = False if int(result[0]) == 0 else True
	return x


def get_cointoss_count(userid: int, guildid: int, type: int):
	"""
	Counts the number of cointoss transactions
	"""
	c = db.cursor()
	c.execute("SELECT COUNT(id) FROM transactions WHERE type=%s and recipient=%s and discord_id=%s and guild_id=%s",
			  (type, userid, userid, guildid))
	res = c.fetchone()
	if res is None:
		return 0
	return res[0]


def get_moolah_history(userid: int, guildid: int):
	c = db.cursor()
	c.execute("SELECT * FROM transactions WHERE recipient=%s or sender=%s and guild_id=%s", (userid, userid, guildid))
	result = c.fetchall()
	if result is None:
		return [], []
	x_time_axis = []
	y_moolah_axis = []
	start = 0
	for entry in result:
		if userid == entry[3]:
			# gain money
			start += entry[2]
			x_time_axis.append(datetime.fromtimestamp(entry[6]))
			y_moolah_axis.append(start)
		elif userid == entry[4]:
			# lose money
			start -= entry[2]
			x_time_axis.append(datetime.fromtimestamp(entry[6]))
			y_moolah_axis.append(start)
	return x_time_axis, y_moolah_axis


db = mydbwrapper.disconnectSafeConnect(config.DB_HOST, config.DB_USER, config.DB_PASS, config.DB_DATABASE)
db.autocommit(True)
member_dict = None
get_member_id_dict()
