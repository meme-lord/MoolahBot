#!/usr/bin/env python
# Stolen from https://stackoverflow.com/questions/207981/how-to-enable-mysql-client-auto-re-connect-with-mysqldb/982873#982873

import logging
import threading

import MySQLdb

reconnect_lock = threading.Lock()
log = logging.getLogger(__name__)


class DisconnectSafeCursor(object):
	db = None
	cursor = None

	def __init__(self, db, cursor):
		self.db = db
		self.cursor = cursor

	def close(self):
		self.cursor.close()

	def execute(self, *args, **kwargs):
		try:
			return self.cursor.execute(*args, **kwargs)
		except MySQLdb.OperationalError as e:
			self.handle_error(e)
			return self.cursor.execute(*args, **kwargs)

	def executemany(self, *args, **kwargs):
		try:
			return self.cursor.executemany(*args, **kwargs)
		except MySQLdb.OperationalError as e:
			self.handle_error(e)
			return self.cursor.executemany(*args, **kwargs)

	def handle_error(self, error):
		log.info(f"SQL Error: {error}")
		if isinstance(error, MySQLdb.OperationalError):
			# if error[0] in [2006, 2002]:
			if reconnect_lock.locked():
				with reconnect_lock:
					log.info("Not reconnecting as another thread should have done it")
					return
			with reconnect_lock:
				log.info("Reconnecting to SQL server")
				self.db.reconnect()
				self.cursor = self.db.cursor()

	def fetchone(self):
		return self.cursor.fetchone()

	def fetchall(self):
		return self.cursor.fetchall()


class DisconnectSafeConnection(object):
	connect_args = None
	connect_kwargs = None
	conn = None
	autocommit = True

	def __init__(self, *args, **kwargs):
		self.connect_args = args
		self.connect_kwargs = kwargs
		self.reconnect()

	def reconnect(self):
		self.conn = MySQLdb.connect(*self.connect_args, **self.connect_kwargs)
		self.conn.autocommit(self.autocommit)

	def cursor(self, *args, **kwargs):
		cur = self.conn.cursor(*args, **kwargs)
		return DisconnectSafeCursor(self, cur)

	def commit(self):
		self.conn.commit()

	def rollback(self):
		self.conn.rollback()

	def autocommit(self, bool):
		self.autocommit = bool
		self.conn.autocommit(bool)


disconnectSafeConnect = DisconnectSafeConnection
