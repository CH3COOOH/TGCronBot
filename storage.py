import yaml
import os
import sys

def load_user_yaml(dir, user_id):
	path = f"{dir}/{user_id}.yaml"
	if not os.path.exists(path):
		return {}
	with open(path, "r", encoding="utf-8") as f:
		return yaml.safe_load(f) or {}

def save_user_yaml(dir, user_id, data):
	os.makedirs(dir, exist_ok=True)
	path = f"{dir}/{user_id}.yaml"
	with open(path, "w", encoding="utf-8") as f:
		yaml.safe_dump(data, f, allow_unicode=True)

def load_config(fpath):
	if not os.path.exists(fpath):
		print("** Cannot find config file. Exit.")
		sys.exit(1)
	with open(fpath, "r", encoding="utf-8") as f:
		return yaml.safe_load(f)