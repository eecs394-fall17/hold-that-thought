from __future__ import print_function
import httplib2
import os

from apiclient import discovery
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
        self.SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
        self.CLIENT_SECRET_FILE = 'client_secret.json'
        self.APPLICATION_NAME = 'Gmail API Python Quickstart'

        self.firebase = firebase.FirebaseApplication('https://fir-demo-184316.firebaseio.com/', None)

    def post_new_users(self):
        self.user_number = 1

        while True: 
            new_user = 'User{0}'.format(self.user_number)
            print ('We are writing this user to database:' + new_user)
            result = self.firebase.post('/users', new_user)
            time.sleep(10)
            self.user_number += 1


    def get_credentials():
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

    def main():
        """Shows basic usage of the Gmail API.

        Creates a Gmail API service object and outputs a list of label names
        of the user's Gmail account.
        """
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)

        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        if not labels:
            print('No labels found.')
        else:
          print('Labels:')
          for label in labels:
            print(label['name'])


    # if __name__ == '__main__':
    #    main()

myObject = gmailQuerier()
myObject.post_new_users()