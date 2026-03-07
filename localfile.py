import yaml
import os
import sys

from logger import Log

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
			return {}
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

