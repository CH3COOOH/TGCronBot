import sys

from actions import Actions
from localfile import FileHandler
from scheduler import Scheduler
from conversation import Conversation
from logger import Log
import watcher

def main():

	if len(sys.argv) != 2:
		print('-----\nUsage: bot <config.yaml>\n-----')
		sys.exit(1)
	CONFIG_PATH = sys.argv[1]

	fh = FileHandler(CONFIG_PATH)
	log = Log(fh.get_loglevel())
	log.print('FileHandler ready.')
	log.print(fh.conf, level=0)

	sch = Scheduler(fh.get_timezone())
	sch.run()
	log.print('Scheduler launched.')

	## Monitor YAML file changes in storage directory
	# watcher.start_watcher(fh, sch)
	# log.print('Storage monitor launched.')

	action = Actions(fh, sch)
	log.print('Action ready. Start Conversation...')

	conv = Conversation(action)
	conv.init_handler()
	conv.run_handler()

if __name__ == "__main__":
	main()
