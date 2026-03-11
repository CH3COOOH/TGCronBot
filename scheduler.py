import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone, all_timezones
from const import *
from logger import Log
from messager import MsgHandler
from localfile import FileHandler

CRON_ALLOWED_PATTERN = re.compile(r'^[0-9\*\-,\/\? ]+$')

def validate_cron(expr: str) -> bool:

	## Please add more exception handler, such as 12:114514

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

class Scheduler:
	def __init__(self, fh: FileHandler, msg_handler: MsgHandler):
		self.fh = fh
		self.timezone = fh.get_timezone()
		self.msgr = msg_handler
		self.log = Log()
		self.scheduler = None

	def __parse_cron(self, expr: str, tz: str):
		parts = expr.split()
		if len(parts) == 5:
			return CronTrigger.from_crontab(expr, timezone=timezone(tz))
		elif len(parts) == 6:
			year, minute, hour, day, month, weekday = parts
			return CronTrigger(
				year=year,
				month=month,
				day=day,
				hour=hour,
				minute=minute,
				day_of_week=weekday,
				timezone=timezone(tz)
			)
		else:
			raise ValueError("** CRON length must be 5 or 6")

	def check_timezone_format(self, s: str):
		if s in all_timezones:
			return True
		else:
			return False

	def run(self):
		self.scheduler = AsyncIOScheduler(
			timezone=timezone(self.timezone),
			job_defaults={
				"misfire_grace_time": 20,
				"coalesce": True
			}
		)
		self.scheduler.start()

	def add_job(self, user_id, name, cron_expr, callback, message, timezone=None):
		if timezone == None:
			trigger = self.__parse_cron(cron_expr, self.timezone)
		else:
			trigger = self.__parse_cron(cron_expr, timezone)
		self.scheduler.add_job(
			callback,
			trigger,
			args=[user_id, message],
			id=f"{user_id}_{name}",
			replace_existing=True
		)

	def remove_job(self, user_id, name):
		job_id = f"{user_id}_{name}"
		try:
			self.scheduler.remove_job(job_id)
		except:
			pass
	
	def purge_job(self, user_id):
		prefix = f"{user_id}_"
		for job in self.scheduler.get_jobs():
			if job.id.startswith(prefix):
				self.scheduler.remove_job(job.id)

	def reload_user_jobs(self, user_id, isPurge=True) -> int:
		if isPurge == True:
			self.log.print(f"Purge user [{user_id}] jobs...", 2)
			self.purge_job(user_id)
		data = self.fh.load_user_yaml(user_id)
		if data == {}:
			## Bad YAML
			return -1
		for name, info in data[KEY_USER_TASKS].items():
			if info.get("enabled", True):
				self.add_job(user_id, name, info["cron"], self.msgr.send_text, info["msg"], timezone=data[KEY_USER_PROFILE][KEY_PROFILE_TIMEZONE])
			else:
				self.remove_job(user_id, name)
		self.log.print(msg=f"User profile [{user_id}] reloaded.", level=1)
		return 0

	def reload_all_jobs(self) -> int:
		self.log.print('Reload jobs from all users...')
		uids = self.fh.get_id_list()
		for uid in uids:
			print(f" -> {uid}")
			if self.reload_user_jobs(uid, isPurge=False) == -1:
				return -1
		return 0