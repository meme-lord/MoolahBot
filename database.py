import MySQLdb
import config
import threading
import logging

log = logging.getLogger(__name__)

# https://mysqlclient.readthedocs.io/


def execute_transaction(type_id, recipient_id, sender_id, amount):
	# Transactions don't affect lifetime_moolah
	amount = abs(int(amount))
	c = db.cursor()

	lock.acquire()  # A more complex version of this would only lock for the users involved in the transaction
	if sender_id != 0:
		# Get sender balance
		c.execute("SELECT balance FROM users WHERE id=%d", (sender_id))
		balance = c.fetchone()
		# Check if sender balance is sufficient
		if balance is None:
			return False, "User does not exist"
		if balance < amount:
			return False, "User has insufficient funds"

	# Execute transaction
	c.execute(
		"INSERT INTO transactions (type, recipient, amount, sender, timestamp) VALUES (%d, %d, %d, %d,UNIX_TIMESTAMP())",
		(type_id, recipient_id, amount, sender_id))
	c.execute("UPDATE users SET balance=balance+%d WHERE id=%d", (amount, recipient_id))
	lock.release()


# users is an array of tuples of (userid, guildid) that are in vc
def vc_moolah_earned(users, moolah_amount):
	moolah_amount = abs(int(moolah_amount))
	c = db.cursor()

	lock.acquire()
	c.executemany(f"UPDATE users SET balance=balance+{moolah_amount} WHERE discord_id=%d AND guild_id=%d", users)
	lock.release()


def moolah_earned(discord_id, guild_id, moolah_amount):
	moolah_amount = abs(int(moolah_amount))
	c = db.cursor()

	lock.acquire()
	c.execute(f"UPDATE users SET balance=balance+%s WHERE discord_id=%s AND guild_id=%s", (moolah_amount, discord_id, guild_id))
	lock.release()


def topdog(guild_id):
	c = db.cursor()
	c.execute("SELECT discord_id, balance FROM users WHERE guild_id=%d ORDER BY balance DESC LIMIT 10", (guild_id))
	return c.fetchall()


def add_user(discord_id, guild_id):
	c = db.cursor()
	c.execute("INSERT INTO users (discord_id, guild_id, balance, lifetime_moolah, user_initialise_time) VALUES (%d, %d, 0, 0, UNIX_TIMESTAMP())",
			  (discord_id, guild_id))
	if guild_id not in member_dict:
		member_dict[guild_id] = set()
	member_dict[guild_id] = discord_id


def add_users(discord_ids, guild_id):
	new_users = list()
	if guild_id not in member_dict:
		member_dict[guild_id] = set()
	for discord_id in discord_ids:
		if discord_id not in member_dict[guild_id]:
			new_users.append((discord_id, guild_id))

	c = db.cursor()
	c.executemany("INSERT INTO users (discord_id, guild_id, balance, lifetime_moolah, user_initialise_time) VALUES (%s, %s, 0, 0, UNIX_TIMESTAMP())",
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


db = MySQLdb.connect(config.DB_HOST, config.DB_USER, config.DB_PASS, config.DB_DATABASE)
db.autocommit(True)
lock = threading.Lock()  # Lock is needed for transaction integrity don't forget to release!
member_dict = None
get_member_id_dict()
