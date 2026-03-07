import asyncio
from telegram import (
	Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
)
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import TimedOut

from localfile import FileHandler
from scheduler import validate_cron, Scheduler

class Actions:
	def __init__(self, fh: FileHandler, sch: Scheduler):
		self.fh = fh
		self.sch = sch
		self.ASK_NAME = 0
		self.ASK_CRON = 1
		self.ASK_MESSAGE = 2
		self.DEL_SELECT = 10
		self.TURN_SELECT_ON = 20
		self.TURN_SELECT_OFF = 21
		self.ALLOWED_USERS = self.fh.get_allowed_users()
		self.bot = Bot(self.fh.get_token())
	
	def dump_token(self):
		return self.fh.get_token()
	
	async def scheduled_send(self, user_id, message):
		# bot = Bot(self.fh.get_token())
		try:
			await self.bot.send_message(chat_id=user_id, text=message)
		except TimedOut:
			await asyncio.sleep(1.5)
			await self.bot.send_message(chat_id=user_id, text=message)

	async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		if self.ALLOWED_USERS != None and (update.effective_user.id not in self.ALLOWED_USERS):
			print(f"** Block user: [{update.effective_user.id}]")
			return
		print(f"User [{update.effective_user.id}] start.")
		await update.message.reply_text(
			"Hi~👋🏻 This is YUI, your time & task assistant !",
		)

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
			return 
		context.user_data["cron"] = cron
		await update.message.reply_text("What message will be sent?")
		return self.ASK_MESSAGE

	async def sub_ask_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user_id = update.effective_user.id
		name = context.user_data["task_name"]
		cron = context.user_data["cron"]
		msg = update.message.text

		data = self.fh.load_user_yaml(user_id)
		data[name] = {"cron": cron, "msg": msg, "enabled": True}
		self.fh.save_user_yaml(user_id, data)

		self.sch.add_job(user_id, name, cron, self.scheduled_send, msg)

		await update.message.reply_text(f"Task added: {name}")
		return ConversationHandler.END
	## ================================

	## ================================
	## Actions for /list
	## --------------------------------
	async def list_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user_id = update.effective_user.id
		data = self.fh.load_user_yaml(user_id)

		if not data:
			await update.message.reply_text("No task yet...")
			return

		text = "Your tasks:\n\n"
		for name, info in data.items():
			status = "✅" if info.get("enabled", True) else "⛔"
			text += f"# {name}\n  Time: {info['cron']}\n  Status: {status}\n  Message: {info['msg']}\n\n"

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

		keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in data.keys()]
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
		data.pop(name, None)
		self.fh.save_user_yaml(user_id, data)

		self.sch.remove_job(user_id, name)

		await query.edit_message_text(f"Task deleted: {name}")
		return ConversationHandler.END
	## ================================

	## ================================
	# /turnon
	async def turnon_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user_id = update.effective_user.id
		data = self.fh.load_user_yaml(user_id)

		off_tasks = [name for name, info in data.items() if not info.get("enabled", True)]
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
		task = data[name]

		task["enabled"] = True
		self.fh.save_user_yaml(user_id, data)

		self.sch.add_job(user_id, name, task["cron"], self.scheduled_send, task["msg"])

		await query.edit_message_text(f"Task enabled: {name}")
		return ConversationHandler.END
	## ================================

	## ================================
	# /turnoff
	async def turnoff_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user_id = update.effective_user.id
		data = self.fh.load_user_yaml(user_id)

		on_tasks = [name for name, info in data.items() if info.get("enabled", True)]
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
		task = data[name]

		task["enabled"] = False
		self.fh.save_user_yaml(user_id, data)

		self.sch.remove_job(user_id, name)

		await query.edit_message_text(f"Task disabled: {name}")
		return ConversationHandler.END
	## ================================
