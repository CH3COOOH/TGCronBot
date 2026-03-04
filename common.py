import sys
from scheduler import add_job, remove_job
from storage import load_user_yaml, load_config
from telegram import Bot

CONFIG_PATH = sys.argv[1]
STORAGE_DIR = sys.argv[2]

app_conf = load_config(CONFIG_PATH)
TOKEN = app_conf["token"]
ALLOWED_USERS = app_conf["allowed"]

async def scheduled_send(user_id, message):
    bot = Bot(TOKEN)
    await bot.send_message(chat_id=user_id, text=message)

def reload_user_jobs(user_id):
    data = load_user_yaml(STORAGE_DIR, user_id)
    for name, info in data.items():
        if info.get("enabled", True):
            add_job(user_id, name, info["cron"], scheduled_send, info["msg"])
        else:
            remove_job(user_id, name)
