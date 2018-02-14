
import yaml

class Config:
	def __init__(self, config_filename):
		with open(config_filename, 'r') as ymlfile:
			self.cfg = yaml.load(ymlfile)
	
	def getSection(self, section):
		return self.cfg[section]
	
	def getParam(self, section, *path):
		sec = self.getSection(section)
		for i in path:
			sec = sec[i]
		return sec
	
def test():
	c = Config('config.yml')
	print c.cfg
	print c.getSection('mysql')
	print c.getParam('mysql', 'host')
	print c.getParam('slack', 'token')

test()