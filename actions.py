import asyncio
from telegram import (
	Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
)
from telegram.ext import ContextTypes, ConversationHandler

from localfile import FileHandler
from scheduler import validate_cron, Scheduler
from logger import Log
from messager import send_text
from const import *

class Actions:
	def __init__(self, fh: FileHandler, sch: Scheduler):
		self.fh = fh
		self.sch = sch
		self.ASK_USER = 0
		self.ASK_TZ = 1
		self.ASK_NAME = 10
		self.ASK_CRON = 11
		self.ASK_MESSAGE = 12
		self.DEL_SELECT = 20
		self.TURN_SELECT_ON = 30
		self.TURN_SELECT_OFF = 31
		self.ALLOWED_USERS = self.fh.get_allowed_users()
		self.bot = Bot(self.fh.get_token())
		self.log = Log(show_level=fh.get_loglevel(), logfile=fh.get_logfile())

	async def __scheduled_send(self, user_id, message):
		await send_text(user_id, message, self.fh, self.log)

	def dump_token(self):
		return self.fh.get_token()

	async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		if self.ALLOWED_USERS != None and (update.effective_user.id not in self.ALLOWED_USERS):
			print(f"** Block user: [{update.effective_user.id}]")
			return
		print(f"User [{update.effective_user.id}] start.")
		await update.message.reply_text(
			"Hi~👋🏻 This is YUI, your time & task assistant !",
		)

	async def user_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		await update.message.reply_text("Hi, how should I call you:")
		return self.ASK_USER
	
	async def sub_ask_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user_id = update.effective_user.id
		user_name = update.message.text.strip()
		data = self.fh.load_user_yaml(user_id)
		data[KEY_USER_PROFILE][KEY_PROFILE_NAME] = user_name
		self.fh.save_user_yaml(user_id, data)
		await update.message.reply_text(f"Roger that, {user_name} !")
		return ConversationHandler.END

	async def tz_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		await update.message.reply_text("Set a new timezone:")
		return self.ASK_TZ
	
	async def sub_ask_tz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user_id = update.effective_user.id
		input_tz = update.message.text.strip()
		if self.sch.check_timezone_format(input_tz) == True:
			data = self.fh.load_user_yaml(user_id)
			data[KEY_USER_PROFILE][KEY_PROFILE_TIMEZONE] = input_tz
			self.fh.save_user_yaml(user_id, data)
			await update.message.reply_text(f"OK, switch to new timezone: [{input_tz}].")
		else:
			await update.message.reply_text("** Bad timezone pattern. Exit.")
		return ConversationHandler.END

	## ================================
	## Actions for /add a new task
	## --------------------------------
	async def add_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		await update.message.reply_text("Give it a name:")
		return self.ASK_NAME

	async def sub_ask_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		context.user_data["task_name"] = update.message.text.strip()
		await update.message.reply_text("When will it be triggered:\n(Pattern: [year] m h d mo w)")
		return self.ASK_CRON

	async def sub_ask_cron(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		cron = update.message.text.strip()
		if not validate_cron(cron):
			await update.message.reply_text("** Bad time pattern. Exit.")
			return ConversationHandler.END
		context.user_data[KEY_TASKS_CRON] = cron
		await update.message.reply_text("What message will be sent?")
		return self.ASK_MESSAGE

	async def sub_ask_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user_id = update.effective_user.id
		name = context.user_data["task_name"]
		cron = context.user_data[KEY_TASKS_CRON]
		msg = update.message.text

		data = self.fh.load_user_yaml(user_id)
		data[KEY_USER_TASKS][name] = {KEY_TASKS_CRON: cron, KEY_TASKS_MSG: msg, KEY_TASKS_ENABLED: True}
		self.fh.save_user_yaml(user_id, data)

		self.sch.add_job(user_id, name, cron, self.__scheduled_send, msg, timezone=data[KEY_USER_PROFILE][KEY_PROFILE_TIMEZONE])
		self.log.print(msg=f"Actions::sub_ask_message New task [{name}] added.", level=0)

		await update.message.reply_text(f"Task added: {name}")

		return ConversationHandler.END
	## ================================

	## ================================
	## Actions for /list
	## --------------------------------
	async def list_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user_id = update.effective_user.id
		data = self.fh.load_user_yaml(user_id)

		text = f"[Your Timezone]\n\n{data[KEY_USER_PROFILE][KEY_PROFILE_TIMEZONE]}\n\n"

		text += "[Your Tasks]\n\n"
		if not data[KEY_USER_TASKS]:
			text += "No task yet..."
		else:
			for name, info in data[KEY_USER_TASKS].items():
				status = "✅" if info.get(KEY_TASKS_ENABLED, True) else "⛔"
				text += f"# {name}\n  Time: {info[KEY_TASKS_CRON]}\n  Status: {status}\n  Message: {info[KEY_TASKS_MSG]}\n\n"

		await update.message.reply_text(text)
	## ================================

	## ================================
	# /del
	async def del_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user_id = update.effective_user.id
		data = self.fh.load_user_yaml(user_id)

		if not data:
			await update.message.reply_text("Nothing can be deleted...")
			return ConversationHandler.END

		keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in data[KEY_USER_TASKS].keys()]
		await update.message.reply_text(
			"Choose a task to delete:",
			reply_markup=InlineKeyboardMarkup(keyboard)
		)
		return self.DEL_SELECT

	async def sub_del_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		query = update.callback_query
		await query.answer()

		user_id = query.from_user.id
		name = query.data

		data = self.fh.load_user_yaml(user_id)
		data[KEY_USER_TASKS].pop(name, None)
		self.fh.save_user_yaml(user_id, data)

		self.sch.remove_job(user_id, name)
		self.log.print(msg=f"Actions::sub_del_select Task [{name}] deleted.", level=0)

		await query.edit_message_text(f"Task deleted: {name}")
		
		return ConversationHandler.END
	## ================================

	## ================================
	# /turnon
	async def turnon_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user_id = update.effective_user.id
		data = self.fh.load_user_yaml(user_id)

		off_tasks = [name for name, info in data[KEY_USER_TASKS].items() if not info.get(KEY_TASKS_ENABLED, True)]
		if not off_tasks:
			await update.message.reply_text("No tasks are disabled.")
			return ConversationHandler.END

		keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in off_tasks]
		await update.message.reply_text(
			"Choose a task to enable:",
			reply_markup=InlineKeyboardMarkup(keyboard)
		)
		return self.TURN_SELECT_ON

	async def sub_turnon_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		query = update.callback_query
		await query.answer()

		user_id = query.from_user.id
		name = query.data

		data = self.fh.load_user_yaml(user_id)
		task = data[KEY_USER_TASKS][name]

		task[KEY_TASKS_ENABLED] = True
		self.fh.save_user_yaml(user_id, data)

		self.sch.add_job(user_id, name, task[KEY_TASKS_CRON], self.__scheduled_send, task[KEY_TASKS_MSG], timezone=data[KEY_USER_PROFILE][KEY_PROFILE_TIMEZONE])
		self.log.print(msg=f"Actions::sub_turnon_select Task [{name}] enabled.", level=0)

		await query.edit_message_text(f"Task enabled: {name}")
		return ConversationHandler.END
	## ================================

	## ================================
	# /turnoff
	async def turnoff_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user_id = update.effective_user.id
		data = self.fh.load_user_yaml(user_id)

		on_tasks = [name for name, info in data[KEY_USER_TASKS].items() if info.get(KEY_TASKS_ENABLED, True)]
		if not on_tasks:
			await update.message.reply_text("No tasks are enabled.")
			return ConversationHandler.END

		keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in on_tasks]
		await update.message.reply_text(
			"Choose a task to disable:",
			reply_markup=InlineKeyboardMarkup(keyboard)
		)
		return self.TURN_SELECT_OFF

	async def sub_turnoff_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		query = update.callback_query
		await query.answer()

		user_id = query.from_user.id
		name = query.data

		data = self.fh.load_user_yaml(user_id)
		task = data[KEY_USER_TASKS][name]

		task[KEY_TASKS_ENABLED] = False
		self.fh.save_user_yaml(user_id, data)

		self.sch.remove_job(user_id, name)
		self.log.print(msg=f"Actions::sub_turnoff_select Task [{name}] disabled.", level=0)

		await query.edit_message_text(f"Task disabled: {name}")
		return ConversationHandler.END
	## ================================
