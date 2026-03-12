from string import Template
from telegram import Bot
from telegram.error import TimedOut
import asyncio
from localfile import FileHandler
from logger import Log
from const import *

class MsgHandler:
	def __init__(self, fh):
		self.fh = fh
		self.log = Log(fh.get_loglevel())
		self.bot = Bot(fh.get_token())
	
	def __var_convert(self, text, user_profile):
		vars = {
			'user': user_profile[KEY_USER_PROFILE][KEY_PROFILE_NAME]
		}
		t = Template(text)
		return t.safe_substitute(vars)

	async def send_text(self, user_id: int, message: str):
		data = self.fh.load_user_yaml(user_id)
		message = self.__var_convert(message, data)

		try:
			await self.bot.send_message(chat_id=user_id, text=message)
		except TimedOut:
			self.log.print(msg="Actions::scheduled_send Timeout. Retry for once...", level=3, write=True)
			await asyncio.sleep(1.5)
			await self.bot.send_message(chat_id=user_id, text=message)
		self.log.print(msg=f"messager::scheduled_send Message for [{user_id}] was sent.", level=1)
