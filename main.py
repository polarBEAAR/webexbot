#!/usr/bin/python
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import pytz
from webexbot import WebExBot
from config import Config

bot = WebExBot(Config('config.yml'))
bot.connect()
#bot.createMeeting("sto1", "Test meeting.", "11/09/2017 10:30:00")
bot.run()
#print bot.getMeetingURL('sto2', '623833859')


