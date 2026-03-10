from telegram import Bot
from telegram.error import TimedOut
from localfile import FileHandler
from logger import Log
from const import *

async def send_text(user_id: int, message: str, fh: FileHandler, log: Log):
	bot = Bot(fh.get_token())
	data = fh.load_user_yaml(user_id)
	message = f"To: {data[KEY_USER_PROFILE][KEY_PROFILE_NAME]}\n{message}"
	try:
		await bot.send_message(chat_id=user_id, text=message)
	except TimedOut:
		log.print(msg="Actions::scheduled_send Timeout. Retry for once...", level=3, write=True)
		await asyncio.sleep(1.5)
		await bot.send_message(chat_id=user_id, text=message)
	log.print(msg=f"messager::scheduled_send Message for [{user_id}] was sent.", level=1)