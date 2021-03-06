from __future__ import print_function
import httplib2
import os
import base64
import email
from email.mime.text import MIMEText

from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from firebase import firebase
import time
import re
import json
import math
import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

class gmailQuerier:
    def __init__(self):
        # If modifying these scopes, delete your previously saved credentials
        # at ~/.credentials/gmail-python-quickstart.json
        self.SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
        self.CLIENT_SECRET_FILE = 'client_secret.json'
        self.APPLICATION_NAME = 'Gmail API Python Quickstart'

        self.firebase = firebase.FirebaseApplication('https://fir-demo-184316.firebaseio.com/', None)

    def post_new_texts(self, service, name, time, newTime, snippet):

        if(self.firebase.get('/users/', name) == None):
            newusermsg = "I'll hold that thought and remind you about it at 7pm tonight. \nFor information on how to use other features like snooze, text Help at any time."
            usertemp = str(name) + "@mms.att.net"
            alert = self.create_message("holdthatthoughtapp@gmail.com", usertemp, "Welcome to HoldThatThought!", newusermsg)
            self.send_message(service, 'me', alert)
        
        self.firebase.post('/users/' + name + '/', {'time': time, 'newTime': newTime, 'message': snippet})

        #if mostRecentMessages is not empty, delete the entries
        mostRecentTextdb = self.firebase.get('/mostRecentMessages/' + name, None)
        if(mostRecentTextdb != None):
            for entry in mostRecentTextdb:
                self.firebase.delete('/mostRecentMessages/' + name, entry)

        self.firebase.post('/mostRecentMessages/' + name + '/', {'mostRecentMessage': snippet})


    def get_credentials(self):
        """Gets valid user credentials from storage.
        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'gmail-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def main(self):
        """Shows basic usage of the Gmail API.
        Creates a Gmail API service object and outputs a list of label names
        of the user's Gmail account.
        """
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)

        while True:
            try:
                messageids = self.list_messages_matching_query(service, 'me', '')
                if not messageids:
                    print ("There are no ids, but the script is still running")
                for ids in messageids:
                    self.get_message(service, 'me', ids['id'])
                
            except KeyboardInterrupt: 
                print ("Keyboard interrupt; stopping script now")
                break

            except errors.HttpError, error:
                print('An error occurred: %s' % error)

            except Exception as err:
                print('An error occurred or there are no new messages: %s' % err)

            self.checkTime(service)
            

    def list_messages_matching_query(self, service, user_id, query=''):
        """List all Messages of the user's mailbox matching the query.
        Args:
            service: Authorized Gmail API service instance.
            user_id: User's email address. The special value "me"
            can be used to indicate the authenticated user.
            query: String used to filter messages returned.
            Eg.- 'from:user@some_domain.com' for Messages from a particular sender.
        Returns:
            List of Messages that match the criteria of the query. Note that the
            returned list contains Message IDs, you must use get with the
            appropriate ID to get the details of a Message.
        """
        try:

            response = service.users().messages().list(userId=user_id,
                                                       q=query).execute()
            messages = []
            if 'messages' in response:
              messages.extend(response['messages'])

            while 'nextPageToken' in response:
              page_token = response['nextPageToken']
              response = service.users().messages().list(userId=user_id, q=query,
                                                 pageToken=page_token).execute()
              messages.extend(response['messages'])

            return messages
        except errors.HttpError, error:
            print('An error occurred within list_messages_matching_query: %s' % error)

    def checkTime(self, service):
        #checks the times of all messages entered into the database to see if its time to send an alert
        usersdb = self.firebase.get('/users', None)
        for user in usersdb:
            all_texts = usersdb.get(user, None)
            for text in all_texts:
                current_text = all_texts.get(text, None)
                snippet = current_text.get('message')
                newTime = current_text.get('newTime')
                localtime = time.asctime( time.localtime(time.time()) )
                if (newTime[:16] == localtime[:16]): # Check if any messages have reached their time
                    if (self.firebase.get('/sentMessages/', user) != None): # Check there are sentMessages in the first place
                        print("-----We found some sentMessages-----")
                        sentMessagesdb = self.firebase.get('/sentMessages/', user)
                        seen_message = False
                        for entry in sentMessagesdb:
                            current_entry = sentMessagesdb.get(entry, None)
                            if (current_entry.get('sentMessage') == snippet):
                                print("We've already seen this message")
                                seen_message = True
                            else:
                                continue
                        if (seen_message == True):
                            print("We have already seen the message and will not send an alert")
                            return 
                        else: # If we haven't seen the message, then send the alert!
                            print("We have not seen the message")
                            userTemp = str(user) + "@mms.att.net"
                            print("This is who we're sending the alert to: " + userTemp)
                            # Check if mostRecentAlert in the database is the same as current snippet 
                            mostRecentAlertdb = self.firebase.get('/mostRecentAlert/', user)
                            for entry in mostRecentAlertdb:
                                current_entry = mostRecentAlertdb.get(entry, None)
                                if (current_entry.get('alertMessage') == snippet):
                                    alert = self.create_message("holdthatthoughtapp@gmail.com", userTemp, "Another reminder", snippet)
                                    break
                                else: 
                                    alert = self.create_message("holdthatthoughtapp@gmail.com", userTemp, "Don't forget about this", snippet)
                                    break
                            self.send_message(service, 'me', alert)
                            print ("We have sent the alert!") 
                            self.firebase.post('/sentMessages/' + user + '/', {'sentMessage': snippet}) # Add entry to sentMessages firebase
                            
                    else: # Else, assume first time user receiving 
                        userTemp = str(user) + "@mms.att.net"
                        if (self.firebase.get('/mostRecentAlert/', user) != None): # We've sent an alert before
                            print("This is the first time we're snoozing!")
                            print("This is who we're sending the alert to: " + userTemp)
                            alert = self.create_message("holdthatthoughtapp@gmail.com", userTemp, "Another reminder", snippet)
                        else:
                            print("This is the first time the user is receiving an alert!")
                            print("This is who we're sending the alert to: " + userTemp)
                            alert = self.create_message("holdthatthoughtapp@gmail.com", userTemp, "Don't forget about this", snippet)
                        self.send_message(service, 'me', alert)
                        print ("We have sent the alert!") 
                        self.firebase.post('/sentMessages/' + user + '/', {'sentMessage': snippet}) # Add entry to sentMessages firebase

    def delete_message(self, service, user_id, msg_id):
        """Delete a Message.
        Args:
            service: Authorized Gmail API service instance.
            user_id: User's email address. The special value "me"
            can be used to indicate the authenticated user.
            msg_id: ID of Message to delete.
        """
        try:
            service.users().messages().trash(userId=user_id, id=msg_id).execute()
            print('Message with id: %s deleted successfully.' % msg_id)
        except errors.HttpError, error:
            print('An error occurred: %s' % error)

    def get_message(self, service, user_id, msg_id):
        """Get a Message with given ID.
        Args:
            service: Authorized Gmail API service instance.
            user_id: User's email address. The special value "me"
            can be used to indicate the authenticated user.
            msg_id: The ID of the Message required.
        Returns:
            A Message.
        """

        try:
            message = service.users().messages().get(userId=user_id, id=msg_id).execute()
            payload = message['payload']
            headers = payload['headers']
            sender = headers[18]
            sent = headers[19]
            name = sender['value']
            time = sent['value']
            text = message['snippet']
            personalTime = 0
            
            
            if(text.lower() == "help"):
                helpmessage = "\nTo snooze \nReply with an amount of time to add. I understand responses like +5m or +135m. \n \nTo assign a specific time to a reminder alert \nAdd '+(timeincrement)m' to the end of the forwarded message \ni.e. 'Can we set up a meeting for later today? +120m'"
                alert = self.create_message("holdthatthoughtapp@gmail.com", name, "Here are some helpful hints:", helpmessage)
                self.send_message(service, 'me', alert)
                self.delete_message(service, 'me', msg_id)

            elif(text[0] == '+'):
                pos = text.lower().find('m')
                if(pos != -1):
                    personalTime = int(text[1:pos])
                    self.findMostRecentEntry(service, name[:10], personalTime)
                    self.delete_message(service, 'me', msg_id) # Deletes the set new time email 

            else: # Else post it to the database 
                ppos = text.lower().find('+')
                print("This is ppos: %s" % ppos)
                mpos = text.lower().find('m', ppos)
                print("This is mpos: %s" % mpos)
                if(ppos != -1 and mpos != -1):
                    print("This should output the +xm: %s" % text[ppos+1:mpos])
                    personalTime = int(text[(ppos+1):mpos])
                    print("This is personalTime: %s" % personalTime)
                newTime = self.format_time(time, personalTime)
                if(ppos != -1):
                    self.post_new_texts(service, name[:10], time, newTime, text[0:ppos])
                else:
                    self.post_new_texts(service, name[:10], time, newTime, text)
                self.delete_message(service, 'me', msg_id)

        except errors.HttpError, error:
            print('An error occurred: %s' % error)

    def findMostRecentEntry(self, service, sender, personalTime):
        result = self.firebase.get('/users', sender)

        alert_entry = {}
        sent_entry = {}
        main_entry = {}
        alert_key = ""
        sent_key = ""

        # Get the mostRecentAlert text
        mostRecentAlertText = ""
        try: # Try seeing if the user has received an alert about their message (not the default app welcome)
            mostRecentAlertdb = self.firebase.get('/mostRecentAlert/' + sender, None)
            for entry in mostRecentAlertdb:
                current_entry = mostRecentAlertdb.get(entry, None)
                mostRecentAlertText = current_entry.get('alertMessage')
        except: # Else, we don't have a mostRecentAlertText
            mostRecentAlertText = ""

        # Get the mostRecentMessage text
        mostRecentSentText = ""
        try: # Try seeing if the user has sent a text already
            mostRecentTextdb = self.firebase.get('/mostRecentMessages/' + sender, None)
            for entry in mostRecentTextdb:
                temp_entry = mostRecentTextdb.get(entry, None)
                mostRecentSentText = temp_entry.get('mostRecentMessage')
        except:
            mostRecentSentText = ""

        for key in result:
            if(result[key]["message"] == mostRecentAlertText):
                alert_entry = result[key]
                alert_key = key
                print("We found the most recent alert message")
                print(alert_entry["message"])

            if(result[key]["message"] == mostRecentSentText):
                sent_entry = result[key]
                sent_key = key
                print("We found the most recent sent message")
                print(sent_entry["message"])

        #compare times
        #save entries (time, newTime, message) corresponding to most recent time
        sent_entry_time = self.format_time(sent_entry["time"], -1)
        formatted_time = datetime.datetime.strptime(sent_entry_time, "%c")

        try: 
            # The person has received an alert before 
            formatted_alert_time = datetime.datetime.strptime(alert_entry["newTime"], "%c")

            # Check if the alert time is newer than the last sent message
            if (formatted_alert_time > formatted_time):
                time = alert_entry["newTime"]
                main_entry = alert_entry
                key = alert_key
                print('You want to snooze an alert')
                newTime = self.calculateSnoozeTime(time, personalTime)
                # Delete the alert so we can send another one later
                sentMessagesdb = self.firebase.get('/sentMessages/' + sender, None)
                for entry in sentMessagesdb:
                    current_entry = sentMessagesdb.get(entry, None)
                    if (current_entry.get('sentMessage') == alert_entry["message"]): 
                        self.firebase.delete('/sentMessages/' + sender, entry)
                    else:
                        pass
            else:
                time = sent_entry["time"]
                main_entry = sent_entry
                key = sent_key
                print('You want to add time to a new message')
                newTime = self.format_time(time, personalTime)
        except Exception as err:
            print('You have not received an alert before')
            time = sent_entry["time"]
            main_entry = sent_entry
            key = sent_key
            newTime = self.format_time(time, personalTime)

        message = main_entry["message"]
        self.firebase.delete('/users/' + sender, key)
        print("We have deleted this key %s" % key)
        self.post_new_texts(service, sender, main_entry["time"], newTime, message)
        print("We have posted a newTime!")

    def calculateSnoozeTime(self, oldTime, addTime):
        formatted_time = datetime.datetime.strptime(oldTime, "%c")
        new_time = formatted_time + datetime.timedelta(minutes=addTime)
        new_time = new_time.strftime("%c") # Converts back to a string
        print("This is the new_time")
        print(new_time)
        return new_time

    def format_time(self, time, personalTime):
        tempList = (re.split(' ', time))
        temptime = tempList[4]
        temphour = int(temptime[0:2])
        tempmin = int(temptime[3:5])
        
        #first, adjust timezone

        if(tempList[6] == '(CDT)' or tempList[6] == '(CST)'):
            temphour = int(temptime[0:2]) #no timezone change
        elif(tempList[6] == '(PDT)' or tempList[6] == '(PST)'):
            temphour = int(temptime[0:2]) + 2 #adding two hours for +2 timezone
        elif(tempList[6] == '(EDT)' or tempList[6] == '(EST)'):
            temphour = int(temptime[0:2]) - 1 #-1 for timezone
        elif(tempList[6] == '(MDT)' or tempList[6] == '(MST)'):
            temphour = int(temptime[0:2]) + 1 #+1 for timezone

        #if no personaltime declared, add one hour as default; otherwise add personalTime to tempmin

        if(personalTime == 0):
            temphour = 19
            tempmin = 0
        if(personalTime > 0):
            #formatting time properly
            addmin = personalTime % 60
            addhour = int(math.floor(personalTime/60))
            temphour = temphour + addhour
            tempmin = tempmin + addmin

            if(tempmin >= 60):
                temphour = temphour + 1
                tempmin = tempmin - 60

        # If personalTime is -1, it will skip above and just format the time 
        if(temphour < 10): 
            temphour = "0" + str(temphour)
            print ("This is temphour {0}".format(temphour))
        if(tempmin < 10):
            tempmin = "0" + str(tempmin)
            print ("This is tempmin {0}".format(tempmin))
        
        temptime = str(temphour) + ":" + str(tempmin) + temptime[5:]
        tempList[4] = temptime
        print ("This is tempList: %s" % tempList)
        timeList = [tempList[0][0:3], tempList[2], tempList[1], tempList[4], tempList[3]]
        return timeList[0] + " " + timeList[1] + " " + timeList[2] + " " + timeList[3] + " " + timeList[4]

    def create_message(self, sender, to, subject, message_text):
        """Create a message for an email.
        Args:
            sender: Email address of the sender.
            to: Email address of the receiver.
            subject: The subject of the email message.
            message_text: The text of the email message.
        Returns:
            An object containing a base64url encoded email object.
        """
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        if(subject != "Here are some helpful hints:" and subject != "Welcome to HoldThatThought!"): # As long as not one of default messages
            try: # Check if we have sent an alert in the past
                mostRecentAlertdb = self.firebase.get('/mostRecentAlert/' + to[:10], None)
                print("We were able to find mostRecentAlertdb")
                for entry in mostRecentAlertdb:
                    self.firebase.delete('/mostRecentAlert/' + to[:10], entry) # Delete current mostRecentAlert
                self.firebase.post('/mostRecentAlert/' + to[:10] + '/', {'alertMessage': message_text}) # Add entry to mostRecentAlert firebase
                print("We have added mostRecentAlert to the database!")
            except Exception as err:
                print("We haven't sent an alert before")
                print(err)
                self.firebase.post('/mostRecentAlert/' + to[:10] + '/', {'alertMessage': message_text}) # Add entry to mostRecentAlert firebase
                print("We have added mostRecentAlert to the database!")
        return {'raw': base64.urlsafe_b64encode(message.as_string())}

    def send_message(self, service, user_id, message):
      """Send an email message.
      Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        message: Message to be sent.
      Returns:
        Sent Message.
      """
      try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        print ('Message Id: %s' % message['id'])
        return message
      except errors.HttpError, error:
        print ('An error occurred: %s' % error)

myObject = gmailQuerier()
myObject.main()