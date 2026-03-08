import os
from telegram import Bot
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from scheduler import Scheduler
from localfile import FileHandler
from logger import Log
from const import *

class YAMLHandler(FileSystemEventHandler):
	def __init__(self, fh: FileHandler, sch: Scheduler):
		self.fh = fh
		self.sch = sch
		self.log = Log(show_level=fh.get_loglevel(), logfile=fh.get_logfile())
	
	async def __scheduled_send(self, user_id, message):
		bot = Bot(self.fh.get_token())
		await bot.send_message(chat_id=user_id, text=message) # type: ignore

	def __reload_user_jobs(self, user_id):
		data = self.fh.load_user_yaml(user_id)
		for name, info in data[KEY_USER_TASKS].items():
			if info.get("enabled", True):
				self.sch.add_job(user_id, name, info["cron"], self.__scheduled_send, info["msg"])
			else:
				self.sch.remove_job(user_id, name)
		self.log.print(msg=f"User profile [{user_id}] reloaded.", level=1)

	def on_modified(self, event):
		if not event.src_path.endswith(".yaml"):
			return
		filename = os.path.basename(event.src_path)
		user_id = filename.replace(".yaml", "")
		self.__reload_user_jobs(user_id)

def start_watcher(fh: FileHandler, sch: Scheduler):
	observer = Observer()
	observer.schedule(YAMLHandler(fh, sch), path=fh.PATH_STORAGE_DIR, recursive=False)
	observer.start()
