#!/usr/bin/python
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import os
from slackclient import SlackClient

#from datetime import datetime
#from dateutil import parser
import time
import datetime
import calendar

import pytz
from googleeventer import GoogleEventer
from room import Room

class WebExBot:
	def __init__(self, config):
		self.config = config
		self.creds = []
		cr = self.config.getSection('rooms')
		for room in cr.keys():
			self.creds.append((room, cr[room]['passwd']))
		#f = open('slack_token', 'rt')
		#self.token = f.read()
		#f.close()
		self.token = self.config.getParam('slack', 'token')
		self.sc = None
		self.chan_name = self.config.getParam('slack', 'channel')
		self.chan = self.chan_name
		self.username = self.config.getParam('slack', 'username')
		print 'creating google eventer'
		self.G = GoogleEventer(self.config)
		print 'google eventer created'
	
	def connect(self):
		self.sc = SlackClient(self.token)
		groups = self.sc.api_call('groups.list', token = self.token)
		for gr in groups['groups']: 
			if gr['name'] == self.chan_name:
				self.chan = gr['id']
		groups = self.sc.api_call('channels.list', token = self.token)
		for gr in groups['channels']:
			if gr['name'] == self.chan_name:
				self.chan = gr['id']
	
	def run(self):
		if self.sc.rtm_connect():
			print("StarterBot connected and running!")
			READ_WEBSOCKET_DELAY = 1
			while True:
				#print 'Next iter'
				events = self.sc.rtm_read()
				for event in events:
					if ('channel' in event and 'text' in event and event.get('type') == 'message'):
						channel = event['channel']
						text = event['text']
						print event
						if channel == self.chan:
							if text == "active":
								print "check started"
								self.sc.api_call("chat.postMessage", as_user="false", channel=self.chan, text='Checking webex rooms', username=self.username)
								att = self.checkWebEx()
								print att
								self.sc.api_call("chat.postMessage", as_user="false", channel=self.chan, text="Current and future meetings:", attachments = att, username=self.username)
							elif text == "help":
								self.sc.api_call("chat.postMessage", as_user="false", channel=self.chan, text='Possible commands are:\nactive - to check active and future meetings\nhelp - to display this message\ncreate|room|name|GMT date', username=self.username)
							elif text[:6] == 'create':
								try:
									params = text.split('|')
									room = params[1]
									name = params[2]
									dat = params[3]
									print room
									print name
									print dat
									dic = self.createMeeting(room, name, dat)
									audio = ""
									for i, j in dic['callin'].items():
										audio += "%s %s\n" % (j, i)
									print 'audio: ', audio
									msg = {}
									msg["mrkdwn_in"] = ["title", "text"]
									msg['title'] = "Message for passing to the customer:"
									msg['text'] = """Meeting time: %s\n
Meeting number: %s\n
Meeting link: %s\n
Host key: %s\n
Audio connection:%s
Access code: %s\n""" % ("%s GMT" % dat, dic['key'], dic['inviteURL'], dic['hostKey'], audio, dic['key'])
									mm = """Meeting time: %s\n
Meeting number: %s\n
Meeting link: %s\n
Host key: %s\n
Audio connection:%s
Access code: %s\n""" % ("%s GMT" % dat, dic['key'], dic['inviteURL'], dic['hostKey'], audio, dic['key'])
									d = mm.strip().split('\n')#
									dd = map(lambda x: {'text' : x, 'mrkdwn_in' : ['text']}, d)
									#print 'msg: ', msg
									self.sc.api_call("chat.postMessage", as_user="false", channel=self.chan, text='Session created. Info: %s' % dic.__str__(), attachments = dd, username=self.username)
								except:
									self.sc.api_call("chat.postMessage", as_user="false", channel=self.chan, text='Error occured during meeting creating', username=self.username)
							else:
								print text
								
				time.sleep(READ_WEBSOCKET_DELAY)
	
	def getMeetingURL(self, room, key):
		for (i, j) in self.creds:
			if i == room:
				r = Room(self.config, i, j)
				return r.getMeetingURL(key)
	
	def checkWebEx(self):
		t = []
		for (u, p) in self.creds:
			#r = Room(u, p, log = (u == "mirantis_operations")):
			r = Room(self.config, u, p, query = True)
			t = t + r.getInfo()
		return t
	
	def createMeeting(self, room, meetingName, meetingUTCTime):
		for (i, j) in self.creds:
			if i == room:
				r = Room(self.config, i, j)
				d = r.createMeeting(meetingName, meetingUTCTime)
				d.update(r.getMeetingURL(d['key']))
				d.update(r.getMeetingDetails(d['key']))
				try:
					self.G.createEvent(time.mktime(datetime.datetime.strptime(meetingUTCTime, '%m/%d/%Y %H:%M:%S').timetuple()), meetingName, i, d['inviteURL'])
				except:
					print 'Google event create error'
				print d
				return d


