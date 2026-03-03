import yaml
import os
import sys

STORAGE_DIR = "storage"
CONFIG_PATH = "config.yaml"

def load_user_yaml(user_id):
	path = f"{STORAGE_DIR}/{user_id}.yaml"
	if not os.path.exists(path):
		return {}
	with open(path, "r", encoding="utf-8") as f:
		return yaml.safe_load(f) or {}

def save_user_yaml(user_id, data):
	os.makedirs(STORAGE_DIR, exist_ok=True)
	path = f"{STORAGE_DIR}/{user_id}.yaml"
	with open(path, "w", encoding="utf-8") as f:
		yaml.safe_dump(data, f, allow_unicode=True)

def load_config():
	if not os.path.exists(CONFIG_PATH):
		print("** Cannot find config file. Exit.")
		sys.exit(1)
	with open(CONFIG_PATH, "r", encoding="utf-8") as f:
		return yaml.safe_load(f)