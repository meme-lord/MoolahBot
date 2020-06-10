import logging
from multiprocessing import Process
from time import sleep

import config
from lib.client import MyClient


def discord_process():
	print('____Discord Subprocess launched!____')
	client = MyClient(command_prefix='!')
	client.run(config.bot_token)


apps = {'discord': discord_process}

if __name__ == '__main__':
	processes = {}


	def start_process(name: str):
		item = apps[name]
		p = Process(target=item)
		p.start()
		processes[name] = (p, item)  # Keep the process and the app to monitor or restart


	for app in apps:
		start_process(app)

	while len(processes) > 0:
		for n in processes.copy():
			(p, a) = processes[n]
			sleep(1)
			alive = p.is_alive()
			exitcode = p.exitcode
			if alive:
				continue
			elif exitcode is None and not alive:  # Not finished and not running
				# Do your error handling and restarting here assigning the new process to processes[n]
				logging.error(a, 'Process is Unable to Start!')
				start_process(n)
			elif exitcode < 0 or exitcode == 3:
				if exitcode < 0:
					logging.error("Process Ended with an error restarting!")
				start_process(n)
			elif exitcode == 42:
				logging.info("Process Restart Called: restarting!")
				start_process(n)
			else:
				print(a, 'Process Completed')
				p.join()  # Allow tidyup
				del processes[n]  # Removed finished items from the dictionary

	# When none are left then loop will end
	print('All Processes are exited.')
