import asyncio
import os
from telegram import (
	Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
	ApplicationBuilder, CommandHandler, MessageHandler,
	ConversationHandler, CallbackQueryHandler, ContextTypes, filters
)

import re
from apscheduler.triggers.cron import CronTrigger

from scheduler import add_job, remove_job
from storage import load_user_yaml, save_user_yaml
from watcher import start_watcher
from common import scheduled_send, TOKEN, ALLOWED_USERS

# Conversation states
ASK_NAME, ASK_CRON, ASK_MESSAGE = range(3)
DEL_SELECT = 10
TURN_SELECT_ON = 20
TURN_SELECT_OFF = 21
CRON_ALLOWED_PATTERN = re.compile(r'^[0-9\*\-,\/\? ]+$')

def validate_cron(expr: str) -> bool:
	expr = expr.strip()
	if not CRON_ALLOWED_PATTERN.match(expr):
		return False
	parts = expr.split()
	if len(parts) == 5:
		try:
			CronTrigger.from_crontab(expr)
			return True
		except Exception:
			return False
	if len(parts) == 6:
		try:
			year, minute, hour, day, month, weekday = parts
			CronTrigger(
				year=year,
				month=month,
				day=day,
				hour=hour,
				minute=minute,
				day_of_week=weekday
			)
			return True
		except Exception:
			return False
	return False

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	print(ALLOWED_USERS)
	if ALLOWED_USERS != None and (update.effective_user.id not in ALLOWED_USERS):
		return
	await update.message.reply_text(
		"Hi~👋🏻 This is YUI, your time & task assistant !",
	)

# /add
async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text("Give it a name:")
	return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
	context.user_data["task_name"] = update.message.text.strip()
	await update.message.reply_text("When will it be triggered:\n(Pattern: [year] m h d mo w)")
	return ASK_CRON

async def ask_cron(update: Update, context: ContextTypes.DEFAULT_TYPE):
	cron = update.message.text.strip()
	if not validate_cron(cron):
		await update.message.reply_text("** Bad time pattern. Please try again.")
		return ASK_CRON
	context.user_data["cron"] = cron
	await update.message.reply_text("What message will be sent?")
	return ASK_MESSAGE

async def ask_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.effective_user.id
	name = context.user_data["task_name"]
	cron = context.user_data["cron"]
	msg = update.message.text

	data = load_user_yaml(user_id)
	data[name] = {"cron": cron, "msg": msg, "enabled": True}
	save_user_yaml(user_id, data)

	add_job(user_id, name, cron, scheduled_send, msg)

	await update.message.reply_text(f"Task added: {name}")
	return ConversationHandler.END

# /list
async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.effective_user.id
	data = load_user_yaml(user_id)

	if not data:
		await update.message.reply_text("No task yet...")
		return

	text = "Your tasks:\n\n"
	for name, info in data.items():
		status = "✅" if info.get("enabled", True) else "⛔"
		text += f"# {name}\n  Time: {info['cron']}\n  Status: {status}\n  Message: {info['msg']}\n\n"

	await update.message.reply_text(text)

# /del
async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.effective_user.id
	data = load_user_yaml(user_id)

	if not data:
		await update.message.reply_text("Nothing can be deleted...")
		return ConversationHandler.END

	keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in data.keys()]
	await update.message.reply_text(
		"Choose a task to delete:",
		reply_markup=InlineKeyboardMarkup(keyboard)
	)
	return DEL_SELECT

async def del_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()

	user_id = query.from_user.id
	name = query.data

	data = load_user_yaml(user_id)
	data.pop(name, None)
	save_user_yaml(user_id, data)

	remove_job(user_id, name)

	await query.edit_message_text(f"Task deleted: {name}")
	return ConversationHandler.END

# /turnon
async def turnon_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.effective_user.id
	data = load_user_yaml(user_id)

	off_tasks = [name for name, info in data.items() if not info.get("enabled", True)]
	if not off_tasks:
		await update.message.reply_text("No tasks are disabled.")
		return ConversationHandler.END

	keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in off_tasks]
	await update.message.reply_text(
		"Choose a task to enable:",
		reply_markup=InlineKeyboardMarkup(keyboard)
	)
	return TURN_SELECT_ON

async def turnon_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()

	user_id = query.from_user.id
	name = query.data

	data = load_user_yaml(user_id)
	task = data[name]

	task["enabled"] = True
	save_user_yaml(user_id, data)

	add_job(user_id, name, task["cron"], scheduled_send, task["msg"])

	await query.edit_message_text(f"Task enabled: {name}")
	return ConversationHandler.END

# /turnoff
async def turnoff_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.effective_user.id
	data = load_user_yaml(user_id)

	on_tasks = [name for name, info in data.items() if info.get("enabled", True)]
	if not on_tasks:
		await update.message.reply_text("No tasks are enabled.")
		return ConversationHandler.END

	keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in on_tasks]
	await update.message.reply_text(
		"Choose a task to disable:",
		reply_markup=InlineKeyboardMarkup(keyboard)
	)
	return TURN_SELECT_OFF

async def turnoff_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()

	user_id = query.from_user.id
	name = query.data

	data = load_user_yaml(user_id)
	task = data[name]

	task["enabled"] = False
	save_user_yaml(user_id, data)

	remove_job(user_id, name)

	await query.edit_message_text(f"Task disabled: {name}")
	return ConversationHandler.END

# Task recovery
async def restore_jobs(app):
	for filename in os.listdir("storage"):
		if not filename.endswith(".yaml"):
			continue
		user_id = filename.replace(".yaml", "")
		data = load_user_yaml(user_id)
		for name, info in data.items():
			if info.get("enabled", True):
				add_job(user_id, name, info["cron"], scheduled_send, info["msg"])

def main():
	start_watcher()
	app = ApplicationBuilder().token(TOKEN).build()

	# Recover tasks from config file
	app.job_queue.run_once(lambda *_: asyncio.create_task(restore_jobs(app)), 0)

	# Conversations
	add_conv = ConversationHandler(
		entry_points=[CommandHandler("add", add_cmd)],
		states={
			ASK_NAME: [MessageHandler(filters.TEXT, ask_name)],
			ASK_CRON: [MessageHandler(filters.TEXT, ask_cron)],
			ASK_MESSAGE: [MessageHandler(filters.TEXT, ask_message)],
		},
		fallbacks=[]
	)

	del_conv = ConversationHandler(
		entry_points=[CommandHandler("del", del_cmd)],
		states={DEL_SELECT: [CallbackQueryHandler(del_select)]},
		fallbacks=[]
	)

	turnon_conv = ConversationHandler(
		entry_points=[CommandHandler("turnon", turnon_cmd)],
		states={TURN_SELECT_ON: [CallbackQueryHandler(turnon_select)]},
		fallbacks=[]
	)

	turnoff_conv = ConversationHandler(
		entry_points=[CommandHandler("turnoff", turnoff_cmd)],
		states={TURN_SELECT_OFF: [CallbackQueryHandler(turnoff_select)]},
		fallbacks=[]
	)

	# --- Normal command handlers ---
	app.add_handler(CommandHandler("start", start))
	app.add_handler(CommandHandler("list", list_cmd))

	# --- Conversation handlers ---
	app.add_handler(add_conv)
	app.add_handler(del_conv)
	app.add_handler(turnon_conv)
	app.add_handler(turnoff_conv)

	app.run_polling()

if __name__ == "__main__":
	main()
