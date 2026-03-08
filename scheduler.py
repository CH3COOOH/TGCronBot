import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone, all_timezones

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

class Scheduler:
	def __init__(self):
		self.timezone = "Asia/Tokyo"
		self.scheduler = None

	def __parse_cron(self, expr: str, tz: str):
		parts = expr.split()
		if len(parts) == 5:
			return CronTrigger.from_crontab(expr)
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
	
	def set_timezone(self, tz):
		self.timezone = tz

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

	def add_job(self, user_id, name, cron_expr, callback, message):
		trigger = self.__parse_cron(cron_expr, self.timezone)
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
	

