import asyncio
import functools
import logging

log = logging.getLogger(__name__)


class EventV2(asyncio.Event):
	def __init__(self, *args, **kwargs):
		super().__init__()
		self.arg = None

	def set(self, val):
		"""Set the internal flag to true. All coroutines waiting for it to
		become true are awakened. Coroutine that call wait() once the flag is
		true will not block at all.
		"""
		self.arg = val
		if not self._value:
			self._value = True
			for fut in self._waiters:
				if not fut.done():
					fut.set_result(True)


def restart(f):
	# Note this decorator does not flush args immediately it works like a queue.
	@functools.wraps(f)
	async def wrapper(self, *args, **kwargs):
		ret = f(self, *args, **kwargs)
		x = await ret
		asyncio.create_task(wrapper(self, *args, **kwargs))
		return x

	return wrapper
