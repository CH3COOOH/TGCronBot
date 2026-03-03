import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from common import reload_user_jobs

class YAMLHandler(FileSystemEventHandler):
	def on_modified(self, event):
		if not event.src_path.endswith(".yaml"):
			return

		filename = os.path.basename(event.src_path)
		user_id = filename.replace(".yaml", "")

		reload_user_jobs(user_id)

def start_watcher():
	observer = Observer()
	observer.schedule(YAMLHandler(), path="storage", recursive=False)
	observer.start()
