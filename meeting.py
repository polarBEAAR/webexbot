#!/usr/bin/python
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import os
from slackclient import SlackClient

import time
import datetime
import calendar

import pytz


class Meeting:
	datefmt = '%m/%d/%Y %H:%M:%S'
	datefmt2 = '%b %d %H:%M'
	def __init__(self, xml_elem, room = None):
		self.room = room
		self.xml_elem = xml_elem
		self.tz = None
		self.remTime = None
		self.name = None
		self.status = None
		self.key = None
		self.hostKey = None
		for i in self.xml_elem.findall('*'):
			#print i
			if i.tag == "{http://www.webex.com/schemas/2002/06/service/meeting}timeZone":
				self.tz = i.text.split(',')[0]
			elif i.tag == "{http://www.webex.com/schemas/2002/06/service/meeting}startDate":
				self.remTime = i.text
			elif i.tag == "{http://www.webex.com/schemas/2002/06/service/meeting}confName":
				self.name = i.text
			elif i.tag == "{http://www.webex.com/schemas/2002/06/service/meeting}status":
				self.status = i.text
			elif i.tag == "{http://www.webex.com/schemas/2002/06/service/meeting}meetingKey":
				self.key = i.text
			elif i.tag == "{http://www.webex.com/schemas/2002/06/service/meeting}hostKey":
				self.hostKey = i.text
		self.details = self.room.getMeetingDetails(self.key)
		self.time_st = time.strptime(self.remTime + ' GMT', self.datefmt + ' %Z')
		print "1: ", time.strftime(self.datefmt, time.gmtime(calendar.timegm(self.time_st)))
		tz_ = self.tz[3:].split(':')
		self.tz_shift = int(tz_[0]) * 60 + int(tz_[1])
		self.time_gmt_fl = calendar.timegm(self.time_st) - self.tz_shift * 60
		self.time_gmt = time.gmtime(self.time_gmt_fl)
		print "2: ", self.__str__()
	
	def getRow(self):
		repeat = 'NONE'
		if self.details['repeat'] == "WEEKLY":
			repeat = ",".join(self.details['days']) + time.strftime(" %H:%M ", self.time_st) + self.tz
		return ([self.name, time.strftime(self.datefmt2, self.time_gmt), self.status, repeat])
	
	def __str__(self):
		s =  "room : %s, key: %s, name: %s, time_gmt: %s, status: %s, time_loc: %s, tz: %s" % (self.room.username, self.key, self.name, time.strftime(self.datefmt, self.time_gmt), self.status, self.remTime, self.tz)
		if self.details['repeat'] == "WEEKLY":
			s += " REPEATED WEEKLY, on %s" % ",".join(self.details['days'])
		return s
	
	def isToday(self):
		return (self.status == 'INPROGRESS') or ((self.time_gmt_fl > time.time()) and (self.time_gmt_fl > time.time() + 24 * 60 * 60))
	
	def isValid(self):
		#return (self.status == 'INPROGRESS') or (self.time_gmt_fl > time.time() + time.timezone) or (self.details["repeat"] != "NO_REPEAT")
		return (self.status == 'INPROGRESS') or (self.time_gmt_fl > time.time()) or (self.details["repeat"] != "NO_REPEAT")
	def getInfo(self):
		res = {}
		res["title"] = self.name
		res["text"] = "*%s* _%s_ %s" % (self.room.username, self.key, self.status)
		if self.details['repeat'] == "WEEKLY":
			res["text"] += "\n_Weekly (" + ",".join(self.details['days']) + time.strftime(" %H:%M ", self.time_st) + self.tz + ")_"
		res["ts"] = "%i" % int(self.time_gmt_fl)
		res["mrkdwn_in"] = ["title", "text"]
		return res


