import asyncio
from telegram.ext import (
	ApplicationBuilder, CommandHandler, MessageHandler,
	ConversationHandler, CallbackQueryHandler, filters
)

from actions import Actions

class Conversation:
	def __init__(self, action: Actions):
		self.action = action
		self.app = ApplicationBuilder().token(action.dump_token()).build()
		## Recover tasks from config file
		self.app.job_queue.run_once(lambda *_: asyncio.create_task(action.restore_jobs(self.app)), 0)
	
	def __init_conv_add(self):
		return ConversationHandler(
			entry_points=[CommandHandler("add", self.action.add_cmd)],
			states={
				self.action.ASK_NAME: [MessageHandler(filters.TEXT, self.action.sub_ask_name)],
				self.action.ASK_CRON: [MessageHandler(filters.TEXT, self.action.sub_ask_cron)],
				self.action.ASK_MESSAGE: [MessageHandler(filters.TEXT, self.action.sub_ask_message)],
			},
			fallbacks=[],
			allow_reentry=True
		)

	def __init_conv_del(self):
		return ConversationHandler(
			entry_points=[CommandHandler("del", self.action.del_cmd)],
			states={self.action.DEL_SELECT: [CallbackQueryHandler(self.action.sub_del_select)]},
			fallbacks=[],
			allow_reentry=True
		)

	def __init_conv_turnon(self):
		return ConversationHandler(
			entry_points=[CommandHandler("turnon", self.action.turnon_cmd)],
			states={self.action.TURN_SELECT_ON: [CallbackQueryHandler(self.action.sub_turnon_select)]},
			fallbacks=[],
			allow_reentry=True
		)

	def __init_conv_turnoff(self):
		return ConversationHandler(
			entry_points=[CommandHandler("turnoff", self.action.turnoff_cmd)],
			states={self.action.TURN_SELECT_OFF: [CallbackQueryHandler(self.action.sub_turnoff_select)]},
			fallbacks=[],
			allow_reentry=True
		)
	
	def init_handler(self):
		self.app.add_handler(CommandHandler("start", self.action.start))
		self.app.add_handler(CommandHandler("list", self.action.list_cmd))
		self.app.add_handler(self.__init_conv_add())
		self.app.add_handler(self.__init_conv_del())
		self.app.add_handler(self.__init_conv_turnon())
		self.app.add_handler(self.__init_conv_turnoff())
		
	def run_handler(self):
		self.app.run_polling()
