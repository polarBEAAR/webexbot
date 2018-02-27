#!/usr/bin/python
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime
import time

class GoogleEventer:
	
	def __init__(self, config):
		self.config = config
		self.SCOPES = self.config.getParam('google', 'scopes')
		self.CLIENT_SECRET_FILE = self.config.getParam('google', 'secret_file')
		self.APPLICATION_NAME = self.config.getParam('google', 'appname')
		self.calendar_name = self.config.getParam('google', 'calendar_name')
		self.credentials = self.get_credentials()
		self.http = self.credentials.authorize(httplib2.Http())
		self.service = discovery.build('calendar', 'v3', http=self.http)
	
	def get_credentials(self):
		"""Gets valid user credentials from storage.

		If nothing has been stored, or if the stored credentials are invalid,
		the OAuth2 flow is completed to obtain the new credentials.

		Returns:
			Credentials, the obtained credential.
		"""
		#home_dir = os.path.expanduser('~')
		#credential_dir = os.path.join(home_dir, '.credentials')
		#if not os.path.exists(credential_dir):
		#	os.makedirs(credential_dir)
		#credential_path = os.path.join(credential_dir, self.config.getParam('google', 'cred_file'))
		credential_path = self.config.getParam('google', 'cred_file')
		self.store = Storage(credential_path)
		credentials = self.store.get()
		flags = []
		if not credentials or credentials.invalid:
			flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
			flow.user_agent = self.APPLICATION_NAME
			if True:
				credentials = tools.run_flow(flow, self.store)
			else: # Needed only for compatibility with Python 2.6
				credentials = tools.run(flow, self.store)
			print 'Storing credentials to ' + credential_path
		return credentials
	
	def createEvent(self, gmtStart, summary, location, desc, duration = 60):
		event = {
			'summary': summary,
			'location': location,
			'description': desc,
			'start': {
				'dateTime': datetime.datetime.fromtimestamp(gmtStart).isoformat(),
				'timeZone': 'UTC',
			},
			'end': {
				'dateTime': datetime.datetime.fromtimestamp(gmtStart + duration * 60).isoformat(),
				'timeZone': 'UTC',
			},
			'reminders': {
				'useDefault': False,
				'overrides': [ ],
			},
		}
		event = self.service.events().insert(calendarId=self.calendar_name, body=event).execute()

def main():
	G = GoogleEventer()
	G.createEvent(time.mktime(time.gmtime()) + 10*60, 'test', 'test room', 'test desc')

if __name__ == '__main__':
    main()
