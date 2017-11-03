from __future__ import print_function
import httplib2
import os
import base64
import email

from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from firebase import firebase
import time

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

        # Adding a log file to save our print statements
        self.log = open('log_GmailAPI_2017_11_02.txt', 'a')
        self.log.write("We have started querying the GmailAPI!" + "\n")

    def post_new_texts(self, name, time, snippet):

        self.firebase.post('/users/' + name + '/', {'time': time, 'message': snippet})
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
            time.sleep(2) #Run the function every 2 seconds to avoid API rate limit error
            try:
                messageids = self.list_messages_matching_query(service, 'me', '')
                if not messageids:
                    print ("Main: There are no ids, but the script is still running")
                    self.log.write("Main: There are no ids, but the script is still running" + "\n")
                    self.log.flush()
                for ids in messageids:
                    print ("Main: before get_message")
                    self.get_message(service, 'me', ids['id'])

            except KeyboardInterrupt: 
                print ("Main: Keyboard interrupt; stopping script now")
                self.log.write("Main: Keyboard interrupt; stopping script now" + "\n")
                self.log.flush()
                break

            except errors.HttpError, error:
                print('Main: An error occurred: %s' % error)
                self.log.write("Main: An error occurred: {0}".format(error) + "\n")
                self.log.flush()

            except Exception as err:
                print('Main: An error occurred or there are no new messages: %s' % err)
                self.log.write("Main: An error occurred or there are no new messages: {0}".format(err) + "\n")
                self.log.flush()
            

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
            # Adding extra print statements to debug API rate limit error 429 (11/2/2017)
            print("list_messages_matching_query: list method called? NOT YET")
            self.log.write("list_messages_matching_query: list method called? NOT YET" + "\n")
            self.log.flush()

            response = service.users().messages().list(userId=user_id,
                                                       q=query).execute()

            # Adding extra print statements to debug API rate limit error 429 (11/2/2017)
            print("list_messages_matching_query: list method called? YES!")
            self.log.write("list_messages_matching_query: list method called? YES!" + "\n")
            self.log.flush()

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
            print('list_messages_matching_query: An error occurred: %s' % error)
            self.log.write("list_messages_matching_query: An error occurred: {0}".format(error) + "\n")
            self.log.flush()

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
            self.log.write("delete_message: Message with id {0} deleted successfully".format(msg_id) + "\n")
            self.log.flush()

        except errors.HttpError, error:
            print('delete_message: An error occurred: %s' % error)
            self.log.write("delete_message: An error occurred: {0}".format(error) + "\n")
            self.log.flush()

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
            print("we got a message {0}".format(message['snippet']))
            payload = message['payload']
            headers = payload['headers']
            sender = headers[18]
            sent = headers[19]
            name = sender['value']
            time = sent['value']
            print('Sender: %s' % name)
            print('Time: %s' % time)
            print('Message snippet: %s' % message['snippet'])
            self.log.write("get_message: Sender: {0}, Time: {1}, Message: {2}".format(name, time, message['snippet']) + "\n")
            self.log.flush()
            self.post_new_texts(name[:10], time, message['snippet'])
            self.delete_message(service, 'me', msg_id)

        except errors.HttpError, error:
            print('get_message: An error occurred: %s' % error)
            self.log.write("get_message: An error occurred: {0}".format(error) + "\n")
            self.log.flush()

myObject = gmailQuerier()
myObject.main()
