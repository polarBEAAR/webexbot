#!/usr/bin/python
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import os
from slackclient import SlackClient
from config import Config
#from datetime import datetime
#from dateutil import parser
import time
import datetime
import calendar

import pytz

from meeting import Meeting

class Room:
	weekDays = {'MONDAY' : 'Mon', 'TUESDAY': 'Tue', 'WEDNESDAY': 'Wed', 'THURSDAY': 'Ths', 'FRIDAY': 'Fri', 'SATURDAY': 'Sat', 'SUNDAY': 'Sun'}
	
	def __init__(self, config, name, password, log = False, query = False):
		self.config = config
		self.sitename = self.config.getParam('webex', 'sitename')
		self.username = name
		self.password = password
		self.meetings = []
		self.url = "https://%s.webex.com/WBXService/XMLService" % self.sitename
		self.log = log
		m_num = 0
		for directory in ['./meetings', './meeting_links']:
			try:
				os.stat(directory)
			except:
				os.mkdir(directory) 
		if query:
			while True:
				(downloaded, total) = self.queryMeetings(m_num + 1)
				print 'downloaded: ', downloaded, ' total: ', total
				#if m_num > 0:
				#	break
				m_num += downloaded
				
				if m_num >= total:
					break
			
	
	def queryMeetings(self, start_from = 1):
		xml = open("templates/room_query.xml").read() % (self.username, self.password, self.sitename, start_from)
		headers = {'Content-Type': 'text/xml'}
		resp = requests.post(self.url, data=xml, headers=headers).text
		tree = ET.fromstring(resp)
		if self.log:
			print xml
			f = open('%s-%s.xml' % (self.username, start_from), 'wt')
			f.write(self.prettify(tree))
			f.close()
		total = None
		returned = None
		try:
			if self.log: 
				print 'analyze started'
				print 'tree:'
				print tree
				
			self.analyzeMeetingXML(tree)
			if self.log: print 'analyze meeting done'
			body = tree.find('{http://www.webex.com/schemas/2002/06/service}body')
			if self.log: print 'body found'
			bodyContent = body.find('{http://www.webex.com/schemas/2002/06/service}bodyContent')
			if self.log: print 'bodyContent found'
			matchingRecords = bodyContent.find("{http://www.webex.com/schemas/2002/06/service/meeting}matchingRecords")
			if self.log: print 'matching records found'
			total = int(matchingRecords.find("{http://www.webex.com/schemas/2002/06/service}total").text)
			if self.log: print 'total calculated'
			returned = int(matchingRecords.find("{http://www.webex.com/schemas/2002/06/service}returned").text)
			if self.log: print 'return calculated'
		except Exception as inst:
			print 'error in queryMeetings'
			print type(inst)
			print inst.args
			print inst
			print '--------------------------------'
			print 'xml:', xml
			print '--------------------------------'
			
			print '--------------------------------'
			returned = 0
			total = 0
		return (returned, total)
	
	def analyzeMeetingXML(self, elem, pref = ''):
		total = None
		returned = None
		if len(pref) < 10:
			for i in elem.findall('*'):
				if i.tag == "{http://www.webex.com/schemas/2002/06/service/meeting}meeting":
					self.meetings.append(Meeting(i, self))
				else:
					self.analyzeMeetingXML(i, pref = pref + " ")
	
	def prettify(self, elem):
		return self.prettifyString(ET.tostring(elem, 'utf-8'))
	
	def prettifyString(self, st):
		#print st
		reparsed = minidom.parseString(st)
		return reparsed.toprettyxml(indent="\t")
	
	def printMeetings(self):
		for i in self.meetings: 
			if i.isValid():
				print i
	
	def checkMeetingDetailsFile(self, key):
		fname = "meetings/%s" % key
		if os.path.isfile(fname):
			f = open(fname, "rt")
			t = f.read()
			f.close()
			return t
		return None
	
	tallnames = {'{http://www.webex.com/schemas/2002/06/service}tollFreeNum': 'Call-in toll-free number (US/Canada)', '{http://www.webex.com/schemas/2002/06/service}tollNum': 'Call-in toll number (US/Canada)'}
	
	def getMeetingDetails(self, key):
		print 'getMeetingDetails: ', key
		xml = open('templates/room_meeting_details.xml', 'rt').read() % (self.username, self.password, self.sitename, key)
		headers = {'Content-Type': 'text/xml'}
		resp = self.checkMeetingDetailsFile(key)
		if resp == None:
			print 'query, key=',key
			resp = requests.post(self.url, data=xml, headers=headers).text
			f = open("meetings/%s" % key, "wt")
			f.write(resp)
			f.close()
		try:
			tree = ET.fromstring(resp)
			prop = {}
			body = tree.find('{http://www.webex.com/schemas/2002/06/service}body')
			bodycontent = body.find('{http://www.webex.com/schemas/2002/06/service}bodyContent')
			hostKey = bodycontent.find('{http://www.webex.com/schemas/2002/06/service/meeting}hostKey')
			print 'hostkey:', hostKey
			repeat = bodycontent.find('{http://www.webex.com/schemas/2002/06/service/meeting}repeat')
			repeattype = repeat.find('{http://www.webex.com/schemas/2002/06/service/meeting}repeatType')
			prop['repeat'] = repeattype.text
			prop['hostKey'] = hostKey.text
			if repeattype.text == "WEEKLY":
				days = []
				dayInWeek = repeat.find('{http://www.webex.com/schemas/2002/06/service/meeting}dayInWeek')
				for i in dayInWeek.findall('*'):
					days.append(self.weekDays[i.text])
				prop['days'] = days
			callindic = {}
			try:
				call = bodycontent.find('{http://www.webex.com/schemas/2002/06/service/meeting}telephony')
				print 'call: ', call
				callin = call.find('{http://www.webex.com/schemas/2002/06/service/meeting}callInNum')
				print 'callin: ', callin
				for i in callin.findall('*'):
					if i.tag in self.tallnames.keys():
						callindic[self.tallnames[i.tag]] = i.text
			except:
				print 'error in searching for call-in numbers'
			prop['callin'] = callindic
		except:
			print 'error in getMeetingsDetails'
			print 'request-----------------------'
			print xml
			print 'responce----------------------'
			print resp
			print '------------------------------'
		return prop
	
	def getMeetingURL(self, key):
		xml = open('templates/room_meeting_URL.xml', 'rt').read() % (self.username, self.password, self.sitename, key)
		headers = {'Content-Type': 'text/xml'}
		fname = "meeting_links/%s" % key
		resp = None
		if os.path.isfile(fname):
			f = open(fname, "rt")
			resp = f.read()
			f.close()
		else:
			resp = requests.post(self.url, data=xml, headers=headers).text
			f = open(fname, "wt")
			f.write(resp)
			f.close()
		tree = ET.fromstring(resp)
		prop = {}
		body = tree.find('{http://www.webex.com/schemas/2002/06/service}body')
		bodycontent = body.find('{http://www.webex.com/schemas/2002/06/service}bodyContent')
		joinurl = bodycontent.find('{http://www.webex.com/schemas/2002/06/service/meeting}joinMeetingURL')
		inviteurl = bodycontent.find('{http://www.webex.com/schemas/2002/06/service/meeting}inviteMeetingURL')
		return {'joinURL': joinurl.text, 'inviteURL': inviteurl.text}
	
	def createMeeting(self, meetingname, meetingUTCTime):
		#timezone 21 = GMT
		xml = open('templates/room_meeting_create.xml', 'rt').read() % (self.username, self.password, self.sitename, meetingname, meetingUTCTime)
		#print xml
		headers = {'Content-Type': 'text/xml'}
		resp = requests.post(self.url, data=xml, headers=headers).text
		tree = ET.fromstring(resp)
		#testtree = ET.ElementTree(tree)
		#print testtree.write('tree.xml'), type(tree)
		body = tree.find('{http://www.webex.com/schemas/2002/06/service}body')
		bodyContent = body.find('{http://www.webex.com/schemas/2002/06/service}bodyContent')
		key = bodyContent.find('{http://www.webex.com/schemas/2002/06/service/meeting}meetingkey')
		print key.text
		iCalendar = bodyContent.find('{http://www.webex.com/schemas/2002/06/service/meeting}iCalendarURL')
		host = iCalendar.find('{http://www.webex.com/schemas/2002/06/service}host')
		return {'key': key.text}
		
	
	def getInfo(self):
		res = []
		for m in self.meetings:
			if m.isValid():
				res.append(m.getInfo())
		return res




if __name__=='__main__':
	test = Room(Config('config.yml'),'sto3','arsUcaus1')
	try:
		test.createMeeting('mmazepa_test','2/10/2020 09:30:00')
	except Exception as exc:
		print exc
