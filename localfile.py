import yaml
import os
import sys

from logger import Log
from const import *

def user_profile_checker(profile: dict) -> bool:
	'''
	<Correct profile>
	profile:
	timezone:
	user:
	tasks:
	<name>:
		cron:
		enabled:
		msg:
	'''
	if set([KEY_USER_PROFILE, KEY_USER_TASKS]).issubset(profile.keys()) == False:
		return False
	if set([KEY_PROFILE_NAME, KEY_PROFILE_TIMEZONE]).issubset(profile[KEY_USER_PROFILE].keys()) == False:
		return False
	for task_name, task_info in profile[KEY_USER_TASKS].items():
		if set([KEY_TASKS_CRON, KEY_TASKS_ENABLED, KEY_TASKS_MSG]).issubset(task_info.keys()) == False:
			return False
	return True

class FileHandler:
	def __init__(self, pthConf):
		self.PATH_CONF = pthConf
		self.conf = self.__load_config()
		self.PATH_STORAGE_DIR = self.conf['storage']
		self.log = Log(show_level=self.get_loglevel(), logfile=self.get_logfile())

	def __load_config(self):
		if not os.path.exists(self.PATH_CONF):
			print("** Cannot find config file. Exit.")
			sys.exit(1)
		with open(self.PATH_CONF, "r", encoding="utf-8") as f:
			return yaml.safe_load(f)
		
	def load_user_yaml(self, user_id):
		path = f"{self.PATH_STORAGE_DIR}/{user_id}.yaml"
		if not os.path.exists(path):
			return {
				KEY_USER_PROFILE: {
					KEY_PROFILE_NAME: 'Dear Master',
					KEY_PROFILE_TIMEZONE: self.get_timezone()
				},
				KEY_USER_TASKS: {}
			}
		with open(path, "r", encoding="utf-8") as f:
			return yaml.safe_load(f) or {}
		self.log.print(msg=f"User profile [{user_id}] loaded.", level=0, write=True)

	def save_user_yaml(self, user_id, data):
		os.makedirs(self.PATH_STORAGE_DIR, exist_ok=True)
		path = f"{self.PATH_STORAGE_DIR}/{user_id}.yaml"
		with open(path, "w", encoding="utf-8") as f:
			yaml.safe_dump(data, f, allow_unicode=True)
		self.log.print(msg=f"Write into user profile [{user_id}].", level=0, write=True)

	def get_allowed_users(self):
		return self.conf['allowed']
	
	def get_timezone(self):
		return self.conf['timezone']

	def get_token(self):
		return self.conf['token']

	def get_logfile(self):
		return self.conf['logfile']

	def get_loglevel(self):
		return self.conf['loglevel']
	
	def get_hotplug(self):
		return self.conf['hotplug_enabled']

