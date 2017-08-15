#!/usr/bin/env python
''' Module for encapsulating requests against the Okta api
    Docs: http://developer.okta.com/docs/sdk/core/python_api_sdk/
'''
import threading
import Queue
import requests
import yaml
import regex

from okta.attdict import Attdict

BASEURL = 'https://example.okta.com'
MAX_REQ_THREADS = 100

class Client(object):
    ''' Abstract client for making Okta api requests
    '''
    def __init__(self, baseurl=BASEURL, api_key=''):
        ''' Initialize the class (and subclasses) with baseurl and api_key, if
            provided
        '''
        self._url = baseurl
        self._headers = {'Accept': 'application/json',
                         'Content-Type': 'application/json',
                         'Authorization': 'SSWS %s' % api_key}
    @classmethod
    def from_config(cls, path_to_yaml):
        ''' Generate a client from a yaml config
        '''
        with open(path_to_yaml, 'r') as conf:
            conf_dict = yaml.load(conf.read())
        return cls(**conf_dict)

    def get(self, req):
        ''' Perform an HTTP GET with request 'req' and class headers
            Return object-like items or None if there was a problem
        '''
        resp = requests.get(req, headers=self._headers)
        if resp.status_code >= 400:
            print 'Problem with request "%s":\n%s' % (req, resp.text)
            return None
        content = resp.json()
        while 'next' in resp.links:
            resp = requests.get(resp.links['next']['url'],
                                headers=self._headers)
            if isinstance(content, dict):
                content.update(resp.json())
            else:
                content += resp.json()
        if isinstance(content, dict):
            return Attdict(content)
        return [Attdict(i) for i in content]

class UserClient(Client):
    ''' Subclass for making specifically Users-related requests
    '''
    def __init__(self, *args, **kwargs):
        ''' Initialize from base class, add subclass-specific uri
        '''
        super(UserClient, self).__init__(*args, **kwargs)
        self._uri = '/api/v1/users'
    def get_users(self):
        ''' Get all users
        '''
        req = self._url + self._uri
        return self.get(req)
    def get_user_by_email(self, email):
        ''' Search and return okta users by email address
            Probably the easiest way to search
        '''
        req = self._url+self._uri+'/'+email
        return self.get(req)

class AppClient(Client):
    ''' Subclass for making specifically App-related requests
    '''
    def __init__(self, *args, **kwargs):
        ''' Initialize from base class, add subclass-specific uri
        '''
        super(AppClient, self).__init__(*args, **kwargs)
        self._uri = '/api/v1/apps'
    def get_apps_by_label(self, label):
        ''' Try to find an application (and its ID) by a human-readable label
        '''
        apps = self.get(self._url+self._uri)
        for app in apps:
            if regex.search(label, app.label, regex.I):
                yield app

    def get_user_from_app(self, app, user=None):
        ''' Get application-context user info, e.g. Role and Profile for given
            user for given application
            Args:
                app: Attdict representing an application or an application ID
                uid: Attdict representing a user or a user ID
        '''
        if isinstance(app, Attdict):
            app = app.id
        uri_suffix = '/%s/users' % app
        if user:
            if isinstance(user, Attdict):
                user = user.id
            uri_suffix += '/%s' % user
        return self.get(self._url+self._uri+uri_suffix)
    def get_apps_by_user(self, uids):
        ''' Get applications for a list of user ids
            Return list of id:apps dict
        '''
        if not isinstance(uids, list):
            uids = [uids]
        idfilter = '?filter=user.id+eq+\"%s\"'
        req_template = self._url+self._uri+idfilter
        def chunks(alist, num):
            ''' Yield successive num-sized chunks from l.
            '''
            for i in xrange(0, len(alist), num):
                yield alist[i:i+num]

        def enqueue(aqueue, uid):
            ''' Function to put requests in a queue and retrieve results later
            '''
            content = self.get(req_template%uid)
            aqueue.put((uid, content))

        queue = Queue.Queue()
        for chunk in chunks(uids, MAX_REQ_THREADS): # limit 100 for now, not sure what Api
                                        # rate-limit is
            threads = []
            for uid in chunk:
                thred = threading.Thread(target=enqueue, args=[queue, uid])
                thred.start()
                threads.append(thred)
            for thred in threads:
                thred.join()

        apps_by_uid = {}
        while not queue.empty():
            apps_by_uid.update(dict((x, y) for (x, y) in [queue.get_nowait()]))
        return apps_by_uid
