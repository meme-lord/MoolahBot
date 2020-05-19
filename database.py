import MySQLdb
import config
import threading

# https://mysqlclient.readthedocs.io/

db = MySQLdb.connect(config.DB_HOST, config.DB_USER, config.DB_PASS, config.DB_DATABASE)
lock = threading.Lock()  # Lock is needed for transaction integrity don't forget to release!


def add_user(discord_id, balance, lifetime_moolah, server_join_time):
	db.execute("INSERT INTO users (id, balance, lifetime_moolah, server_join_time) VALUES (%d, %d, %d, %d)",
				(discord_id, balance, lifetime_moolah, server_join_time))


def execute_transaction(type_id, recipient_id, sender_id, amount):
	# Transactions don't affect lifetime_moolah
	amount = abs(int(amount))
	c = db.cursor()

	lock.acquire()
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
	c.execute("INSERT INTO transactions (type, recipient, amount, sender, timestamp) VALUES (%d, %d, %d, %d,UNIX_TIMESTAMP())",
			  (type_id, recipient_id, amount, sender_id))
	c.execute("UPDATE users SET balance=balance+%d WHERE id=%d", (amount, recipient_id))
	lock.release()


# users is an array of user ids that are in vc
def vc_moolah_earned(users, moolah_amount):
	moolah_amount = abs(int(moolah_amount))
	c = db.cursor()

	lock.acquire()
	c.executemany(f"UPDATE users SET balance=balance+{moolah_amount} WHERE id=%d", users)
	lock.release()


def topdog():
	c = db.cursor()
	c.execute("SELECT id, balance FROM users ORDER BY balance DESC LIMIT 10")
	return c.fetchall()

