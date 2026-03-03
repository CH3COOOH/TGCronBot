from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

DEFAULT_TZ = "Asia/Tokyo"

scheduler = AsyncIOScheduler(timezone=timezone(DEFAULT_TZ))
scheduler.start()

def parse_cron(expr: str, tz: str):
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

def add_job(user_id, name, cron_expr, callback, message):
	# trigger = CronTrigger.from_crontab(cron_expr, timezone=timezone(DEFAULT_TZ))
	trigger = parse_cron(cron_expr, DEFAULT_TZ)
	scheduler.add_job(
		callback,
		trigger,
		args=[user_id, message],
		id=f"{user_id}_{name}",
		replace_existing=True
	)

def remove_job(user_id, name):
	job_id = f"{user_id}_{name}"
	try:
		scheduler.remove_job(job_id)
	except:
		pass
