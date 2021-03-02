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
		self.token = self.config.getParam('slack', 'token')
		self.sc = None
		self.chan_name = self.config.getParam('slack', 'channel')
		self.chan = self.chan_name
		self.username = self.config.getParam('slack', 'username')
		print 'creating google eventer'
		self.G = GoogleEventer(self.config)
		print 'google eventer created'
	
	def connect(self):
		print 'connect:'
		self.sc = SlackClient(self.token)
  		print self.token, type(self.token)
#		groups = self.sc.api_call('conversations.list', token = self.token, exclude_archived = True, types = 'public_channel', limit = 500, cursor='dGVhbTpDNjdONkVaTDc=')
#		print groups['response_metadata']
#		for gr in groups["channels"]:
#                        print gr["name"]
#                        if gr["name"]=='webexbot':
#                    		print gr["id"] 
#			if gr["name"] == self.chan_name:
#                                print  gr["id"]
				#print 'private channel found'
#				self.chan = gr["id"]
                channel = self.sc.api_call('conversations.info', token = self.token, channel = 'C990L1WCD')
                print channel['channel'], channel['channel']['id'], '\nchannel detected'
                self.chan = channel['channel']['id']
		self.sc.api_call("chat.postMessage", as_user="false", channel=self.chan, text='Bot connected', username=self.username)
		#groups = self.sc.api_call('channels.list', token = self.token)
		#for gr in groups['channels']:
		#	if gr['name'] == self.chan_name:
		#		self.chan = gr['id']
		#		print 'public channel found'
	
	def run(self):
		if self.sc.rtm_connect():
			print("StarterBot connected and running!")
			READ_WEBSOCKET_DELAY = 1
			while True:
				events = self.sc.rtm_read()
				for event in events:
					if ('channel' in event and 'text' in event and event.get('type') == 'message'):
						channel = event['channel']
						text = event['text']
						if ('user' in event):
							user_name = self.userName(event['user'])
						else:
							user_name = 'Noname'
						if channel == self.chan:
							if text == "active":
								print "check started"
								self.sc.api_call("chat.postMessage", as_user="false", channel=self.chan, text='Checking webex rooms', username=self.username)
								att = self.checkWebEx()
								self.sc.api_call("chat.postMessage", as_user="false", channel=self.chan, text="Current and future meetings:", attachments = att, username=self.username)
							elif text == "help":
								self.sc.api_call("chat.postMessage", as_user="false", channel=self.chan, text='Possible commands are:\nactive - to check active and future meetings\nhelp - to display this message\ncreate|room|name|GMT(UTC) date', username=self.username)
							elif text[:6] == 'create':
								try:
									params = text.split('|')
									room = params[1]
									name = params[2]
									dat = params[3]
									print room, name, dat
									dic = self.createMeeting(room, name, dat,user_name)
									print 'createMeeting finished'
									audio = ""
									for i, j in dic['callin'].items():
										audio += "%s %s\n" % (j, i)
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
									print Exception
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
		#logins = self.creds.keys()
		#logins.sort()
		self.creds.sort()
		for (u, p) in self.creds:
			r = Room(self.config, u, p, query = True)
			t = t + r.getInfo()
		return t
			
	
	def userName(self, userID):
		userList = self.sc.api_call("users.list", channel = self.chan)
		if ('members' in userList):
			for user in userList['members']:
				if (userID == user.get('id')):
					name = user['name']
					return name
		return None
	
	
	def createMeeting(self, room, meetingName, meetingUTCTime, user_name):
		print meetingUTCTime
		for (i, j) in self.creds:
			if i == room:
				r = Room(self.config, i, j)
				try:
					d = r.createMeeting(meetingName, meetingUTCTime)
					d.update(r.getMeetingURL(d['key']))
					d.update(r.getMeetingDetails(d['key']))
				except Exception as tesexc:
					print tesexc
				try:
					self.G.createEvent(time.mktime(datetime.datetime.strptime(meetingUTCTime,'%m/%d/%Y %H:%M:%S').timetuple()), meetingName, i, d['inviteURL'],user_name )
				except Exception as inst:
					print type(inst)     # the exception instance
					print inst.args      # arguments stored in .args
					print inst 
					print 'Google event create error'
					raise
				print d
				return d


