import time

class Log:
	def __init__(self, show_level=1, logfile=None):
		self.show_level = show_level
		self.level_map = ['DEBUG', 'INFO', 'WARN', 'ERROR']
		self.logfile = logfile

	def print(self, msg, level=1, write=False) -> int:
		if self.show_level > level:
			return 1
		localtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
		msg = '[%s][%s] %s' % (localtime, self.level_map[level], msg)
		print(msg)
		if write == True:
			if self.logfile == None:
				print('** Logfile is not set. Ignore.')
				return 1
			try:
				with open(self.logfile, 'a', encoding='utf-8') as o:
					o.write(msg + '\n')
			except:
				print('** Unable to write out logfile. Ignore.')
				return 1
		return 0