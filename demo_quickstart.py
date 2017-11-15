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
        self.CLIENT_SECRET_FILE = 'demo_client_secret.json'
        self.APPLICATION_NAME = 'Gmail API Python Quickstart'

        self.firebase = firebase.FirebaseApplication('https://fir-demo-184316.firebaseio.com/', None)
        self.sentMessages = [] 

        # Adding a log file to save our print statements

    def post_new_texts(self, name, time, newTime, snippet):

        self.firebase.post('/users/' + name + '/', {'time': time, 'newTime': newTime, 'message': snippet})
        newresult = self.firebase.get('/users/', name)
        print('We have added this entry: %s' % newresult)


        '''print("In post new texts: %s" % name)
        result = self.firebase.get('/users/', name, snippet)
        if result is not None:
            print('We found a user')
        else:
            print('We did not find ')
            self.firebase.post('/users/' + name + '/', {'time': time, 'message': snippet})
            newresult = self.firebase.get('/users/', name)
            print('We have added this entry: %s' % newresult)'''


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
                                       'demo-gmail-python-quickstart.json')

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
        localtime = time.asctime( time.localtime(time.time()) )
        print ('Local current time: %s' % localtime)
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

        usersdb = self.firebase.get('/users', None)
        for user in usersdb:
            all_texts = usersdb.get(user, None)
            for text in all_texts:
                current_text = all_texts.get(text, None)
                snippet = current_text.get('message')
                newTime = current_text.get('newTime')
                localtime = time.asctime( time.localtime(time.time()) )
                if (newTime[:16] == localtime[:16]):
                    print(self.sentMessages)
                    print(snippet)
                    if(not snippet in self.sentMessages):
                        print ("Before create message")
                        userTemp = str(user) + "@mms.att.net"
                        print("This is who we're sending the alert to: " + userTemp)
                        alert = self.create_message("demoholdthatthought@gmail.com", userTemp, "Don't forget about this", snippet)
                        self.send_message(service, 'me', alert)
                        print ("We have sent the alert!")
                        url = 'users' + '/' + user + '/' + text
                        self.sentMessages.append(str(snippet))
                    else:
                        print ("We've already seen this message")
                    
            '''
            for text in users.get().each():
                snippet = text.get('/message')
                newTime = text.get('/newTime')
                print('This is the snippet ' + snippet)
                print('This is the newTime ' + newTime)
            '''

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
            print('Sender: %s' % name)
            print('Time: %s' % time)

            print('Message snippet: %s' % message['snippet'])
            newTime = self.format_time(time)
            self.post_new_texts(name[:10], time, newTime, message['snippet'])
            self.delete_message(service, 'me', msg_id)

        except errors.HttpError, error:
            print('An error occurred: %s' % error)

    def format_time(self, time):
        tempList = (re.split(' ', time))
        temptime = tempList[4]
        temphour = int(temptime[0:2])
        if(tempList[6] == '(CDT)' or tempList[6] == '(CST)'):
            temphour = int(temptime[0:2]) + 1 #adding one hour for alert
        elif(tempList[6] == '(PDT)' or tempList[6] == '(PST)'):
            temphour = int(temptime[0:2]) + 3 #adding three hours for +2 timezone and +1 alert
        elif(tempList[6] == '(EDT)' or tempList[6] == '(EST)'):
            temphour = int(temptime[0:2]) #-1 for timezone +1 for alert
        elif(tempList[6] == '(MDT)' or tempList[6] == '(MST)'):
            temphour = int(temptime[0:2]) + 2 #+1 for timezone +1 for alert
        if(temphour < 10): 
            temphour = "0" + str(temphour)
            print ("This is temphour {0}".format(temphour))
            '''tempmin = int(temptime[3:5]) + 1;
            if(tempmin < 10):
                tempmin = "0" + str(tempmin)
            print ("This is tempmin {0}".format(tempmin))
            temptime = str(temphour) + ":" + str(tempmin) + temptime[5:]'''
        temptime = str(temphour) + temptime[2:]
        tempList[4] = temptime
        print ("This is tempList: %s" % tempList)
        timeList = [tempList[0][0:3], tempList[2], tempList[1], tempList[4], tempList[3]]
        return timeList[0] + " " + timeList[1] + "  " + timeList[2] + " " + timeList[3] + " " + timeList[4]

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
