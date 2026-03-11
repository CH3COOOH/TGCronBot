import sys

from actions import Actions
from localfile import FileHandler
from scheduler import Scheduler
from conversation import Conversation
from logger import Log
from messager import MsgHandler
# import watcher

def main():

	if len(sys.argv) != 2:
		print('-----\nUsage: bot <config.yaml>\n-----')
		sys.exit(1)
	CONFIG_PATH = sys.argv[1]

	fh = FileHandler(CONFIG_PATH)
	log = Log(fh.get_loglevel())
	log.print('FileHandler ready.')
	log.print(fh.conf, level=0)

	msg_handler = MsgHandler(fh)
	log.print('MsgHandler ready.')

	sch = Scheduler(fh, msg_handler)
	sch.run()
	sch.reload_all_jobs()
	log.print('Scheduler launched.')

	action = Actions(fh, sch, msg_handler)
	log.print('Action ready. Start Conversation...')

	conv = Conversation(action)
	conv.init_handler()
	conv.run_handler()

if __name__ == "__main__":
	main()
