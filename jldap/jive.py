#!/usr/bin/env python
''' Module/classes for posting information to a Jive instance
'''

import json
import requests
requests.packages.urllib3.disable_warnings()

THINGTYPES = ['contents', 'places', 'people']
DEFAULT_URL = 'https://domain.example.com/api/core/v3'

class PosterError(Exception):
    ''' Custom Exception for handling customer problems '''
    def __init__(self, *args, **kwargs):
        super(PosterError, self).__init__(*args, **kwargs)

class JiveApi(object):
    '''Class for GETing, PUTing, and POSTing to brewspace (or any Jive instance
    with api v3).
    '''
    def __init__(self,
                 user=None,
                 password=None,
                 url=DEFAULT_URL):
        '''Set up for using the Jive API.
           Collect user/password if they exist and base site url.
        '''
        self._user = user
        self._password = password
        self._url = url
        self.headers = {'content-type': 'application/json'}

    @property
    def user(self):
        ''' Return user
        '''
        return self._user
    @user.setter
    def user(self, usr_):
        self._user = usr_
    @property
    def password(self):
        ''' Return password
        '''
        return self._password
    @password.setter
    def password(self, pswd):
        self._password = pswd
    @property
    def url(self):
        ''' Return the url
        '''
        return self._url
    @url.setter
    def url(self, url_):
        self._url = url_

    def search(self, search, contentonly=False, thingtype='contents'):
        '''As safely as possible, get something from the site.
           Can be contents, places, or people.
           Instead of mirroring the API exactly, can ask for only content.
        '''
        if thingtype not in THINGTYPES:
            thingtype = 'contents'
        query = self.url + '/search/%s?filter=search("%s")'
        query = query % (thingtype, search)
        returnedpage = requests.get(query,
                                    auth=(self.user,
                                          self.password),
                                    headers=self.headers)
        try:
            if returnedpage.text.startswith('throw'):
                # stupid """header""" before json
                text = '\n'.join(returnedpage.text.split('\n')[1:])
                data = json.loads(text)
            else:
                data = json.loads(returnedpage.text)
        except Exception as err:
            msg = (err.message + '. %s returned HTTP %s' %
                   (self.url, returnedpage.status_code))
            raise PosterError(msg)
        for i in data['list']:
            if thingtype == 'contents' and i['subject'] == search:
                if contentonly:
                    return i['content']
                else:
                    return i
            elif thingtype == 'places' and i['name'] == search:
                return i
        return data

    def post(self, subject, html, place=None):
        '''As safely as possible, POST to the site.
           Will create item with name of 'subject' with given html in given
           place.
        '''
        url = self.url + '/contents'
        content = {'type' : 'document',
                   'status' : 'published',
                   'subject' : subject,
                   'content' : {'type' : 'text/html',
                                'text' : html
                               }
                  }

        if place:
            try:
                place_id = self.search(place, thingtype='places')['placeID']
            except KeyError:
                msg = ('Could not find placeID for search %s. Please try again.'
                       % place)
                raise PosterError(msg)
            content['visibility'] = 'place'
            content['parent'] = self.url + '/places/%s' % place_id
        params = json.dumps(content)
        returned_page = requests.post(url,
                                      data=params,
                                      auth=(self.user, self.password),
                                      headers=self.headers)
        try:
            json_data = json.loads(returned_page.text)
            return json_data['resources']['html']['ref']
        except KeyError as err:
            msg = (err.message + '. %s returned HTTP %s' %
                   (self.url, returned_page.status_code))
            raise PosterError(msg)

    def put(self, subject, html):
        '''As safely as possible, PUT to the site.
           Will update site content with name of subject with given html.
        '''

        content = self.search(subject)
        content['content']['text'] = html
        url = self.url + '/contents/%s' % content['contentID']
        params = json.dumps(content)
        returned_page = requests.put(url,
                                     data=params,
                                     auth=(self.user, self.password),
                                     headers=self.headers)
        try:
            json_data = json.loads(returned_page.text)
            return json_data['resources']['html']['ref']
        except Exception as err:
            msg = (err.message + '. %s returned HTTP %s' %
                   (self.url, returned_page.status_code))
            raise PosterError(msg)
