import asyncio
import functools
import logging

log = logging.getLogger(__name__)


class EventV2(asyncio.Event):
	def __init__(self, *args, **kwargs):
		super().__init__()
		self.arg = None
		self._value = True

	async def set(self, val):
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
		await asyncio.sleep(0.01)  # give time for asyncio calls to be run.


def on_vc_moolah_update(f):
	"""
	This decorator wraps a function it is attached to to wait for the event to fire
	It also restarts the function when it is finished to keep listening.
	"""

	@functools.wraps(f)
	async def wrapper(self, *args, **kwargs):
		onvc = self.bot.events['cogs.moolah']['moolahVoice']
		await onvc.wait()
		onvc.clear()
		ret = f(self, *args, **kwargs, var=onvc.arg)
		x = await ret
		asyncio.create_task(wrapper(self, *args, **kwargs))
		return x

	return wrapper


def on_cointoss_end(f):
	"""
	This decorator wraps a function it is attached to to wait for the event to fire
	It also restarts the function when it is finished to keep listening.
	"""

	@functools.wraps(f)
	async def wrapper(self, *args, **kwargs):
		onvc = self.bot.events['cogs.cointoss']['cointoss']
		await onvc.wait()
		onvc.clear()
		ret = f(self, *args, **kwargs, var=onvc.arg)
		x = await ret
		asyncio.create_task(wrapper(self, *args, **kwargs))
		return x

	return wrapper


def on_slots_end(f):
	"""
	This decorator wraps a function it is attached to to wait for the event to fire
	It also restarts the function when it is finished to keep listening.
	"""

	@functools.wraps(f)
	async def wrapper(self, *args, **kwargs):
		onvc = self.bot.events['cogs.slots']['slots']
		await onvc.wait()
		onvc.clear()
		ret = f(self, *args, **kwargs, var=onvc.arg)
		x = await ret
		asyncio.create_task(wrapper(self, *args, **kwargs))
		return x

	return wrapper
