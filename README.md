# HoldThatThought

# System Requirements
Python 2.7 or greater

# Synopsis
HoldThatThought is a text bot that allows users to forward messages that they wish to be reminded about at a later time. It uses the Gmail API to query an inbox and records forwarded messages into a firebase.

# Code Example
Users send forwarded messages to a central Gmail account; when running, the text bot script checks for new messages and adds messages to a Firebase database under the user’s phone number. When the local time matches an assigned alert time for any of the messages in Firebase, the script triggers the Gmail API to send an alert to the appropriate user. 

	for entry in mostRecentAlertdb:
		current_entry = mostRecentAlertdb.get(entry, None)
		if (current_entry.get('alertMessage') == snippet):
		    alert = self.create_message("holdthatthoughtapp@gmail.com", userTemp, "Another reminder", snippet)
		    break
		else: 
		    alert = self.create_message("holdthatthoughtapp@gmail.com", userTemp, "Don't forget about this", snippet)
		    break
	self.send_message(service, 'me', alert)

When users forward a text to the Gmail account, the message will be automatically assigned a default time in the database. To change the default time, change the following part of the code. 

	def format_time(self, time, personalTime):
		if(personalTime == 0):
            		temphour = 19
            		tempmin = 0

First time users will receive a welcome message on how to use the text bot. In addition, users who text “Help” can receive information on how to use the text bot. These can be personalized within the code: 

	def post_new_texts(self, service, name, time, newTime, snippet):
		if(self.firebase.get('/users/', name) == None):
		    newusermsg = "I'll hold that thought and remind you about it at 7pm tonight. \nFor information on how to use other features like snooze, text Help at any time."
		    usertemp = str(name) + "@mms.att.net"
		    alert = self.create_message("holdthatthoughtapp@gmail.com", usertemp, "Welcome to HoldThatThought!", newusermsg)
		    self.send_message(service, 'me', alert)

Users can also snooze alerts by texting +(time increment)m. For example, texting ‘+5m’ will snooze an alert for five minutes. This adds five minutes to the last alert time. 
	
	def checkTime(self, service):
		for entry in mostRecentAlertdb:
			current_entry = mostRecentAlertdb.get(entry, None)
			if (current_entry.get('alertMessage') == snippet):
			    alert = self.create_message("holdthatthoughtapp@gmail.com", userTemp, "Another reminder", snippet)
			    break
	

# Motivation
We developed this text bot as part of the Agile Software Project Management and Development course at Northwestern University in Fall 2017 by Professor Chris Riesbeck. We designed this text bot to help busy professionals keep track of incoming messages. 

# Installation
We recommend using a remote machine (e.g., a droplet on Digital Ocean) and Screen to run the script continuously and collect incoming user texts. Clone the repository to where you will be running the script. 

## Install Python Dependencies
To run the script, make sure you have installed the following dependencies:
	
	$ pip install httplib2
	$ pip install mime
	$ pip install --upgrade google-api-python-client
	$ pip install --upgrade oauth2client
	$ sudo pip install requests==1.1.0
	$ sudo pip install python-firebase

## Setting up Firebase and Gmail Account
Then, create a central Gmail account that will receive all forwarded texts from users at mail.google.com. Next, set up a Firebase project at https://firebase.google.com/. Turn on the Gmail API for your application by following the instructions on this webpage and register your application using your Firebase project. You will download a JSON file with the client ID and secret key needed for running the text bot. Save this JSON file as “client_secret.json” in the repository. 

Modify the following parts of quickstart.py to connect your script to Firebase and your Gmail account: 

	def __init__(self):
		# If modifying these scopes, delete your previously saved credentials
		# at ~/.credentials/gmail-python-quickstart.json
		self.SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
		self.CLIENT_SECRET_FILE = 'client_secret.json'
		self.APPLICATION_NAME = 'Gmail API Python Quickstart'
        	self.firebase = firebase.FirebaseApplication('https://fir-demo-184316.firebaseio.com/', None)
		
	
	alert = self.create_message("holdthatthoughtapp@gmail.com", usertemp, "Welcome to HoldThatThought!", newusermsg) #change the first parameter of any reference to self.create_message so that it refers to your newly created inbox

## Running the App
To begin the text bot, simply run:
	
	python quickstart.py 

When running the script for the first time, the Gmail API will prompt you to sign in to your Gmail account in a browser window. Follow the instructions to sign in to your Gmail account. If you need to connect the API to a different account in the future, make sure to remove your saved credentials file first at ~/.credentials/gmail-python-quickstart.json.
API Reference
You may reference the following documentation for using Gmail API and Firebase in Python. 

# Known Bugs
The script currently only works when users are in the same timezone as where the script is being run. 
This project currently only works for AT&T iPhone users. 

At random intervals, the code will stop running and throw an SSL error. When this occurs, you can just restart the code and no data will be lost. 

If users request multiple messages with the same subject line and body (i.e. the “help” message), Gmail’s spam detection algorithm will mark requests to send such messages as spam. When this occurs, these messages will show up as “sent” in the outbox, but will not appear on the user’s phone. 

# License
Copyright 2017 Abitha Ramachandran, Eureka Foong

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0 

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

