#!/usr/bin/env python
''' Abstract the procurement of an AWS client somewhat.
'''
import os
import getpass
import string
import random
import ConfigParser
from collections import defaultdict
import boto3
import botocore

DEFAULT_SHAREDCREDS = os.path.expanduser('~/.aws/credentials')
ID_LEN = 8 # *shrug* power of 2

def id_generator(size=ID_LEN, chars=string.ascii_uppercase + string.digits):
    ''' Generate unique ids for role assumption session names
        Tag with OS username for best-effort session tracking
    '''
    uid = ''.join(random.choice(chars) for _ in range(size))
    return '%s-%s' % (getpass.getuser(), uid)

class ProfileNode(object):
    def __init__(self, name=None, values=defaultdict(str)):
        self._name = name
        self._region = values['region']
        self._values = values
        self._clienttype = 'iam'
    @property
    def type(self):
        return self._clienttype
    @type.setter
    def type(self, clienttype):
        self._clienttype = clienttype
    def __getitem__(self, key):
        return self._values[key]
    def get_client(self):
        if 'role_arn' in self._values:
            intermediate = (boto3
                            .client('sts')
                            .assume_role(RoleArn = self._values['role_arn'],
                                         RoleSessionName = id_generator()))
            creds = intermediate['Credentials']
            kwargs = {'aws_access_key_id': creds['AccessKeyId'],
                      'aws_secret_access_key': creds['SecretAccessKey'],
                      'aws_session_token': creds['SessionToken']}
        else:
            kwargs = {'aws_access_key_id': self._values['aws_access_key_id'],
                      'aws_secret_access_key': self._values['aws_secret_access_key']}
        self._client = boto3.client(self.type, **kwargs)
        return self._client

class Credentials(object):
    @classmethod
    def from_file(cls, path=DEFAULT_SHAREDCREDS):
        parser = ConfigParser.ConfigParser()
        parser.read(path)
        creds = cls()
        for key, val in parser.__dict__['_sections'].items():
            creds.add(key, **val)
        return creds
    def __init__(self):
        self._creds = {}
    def add(self, name, **kwargs):
        ''' Add a set of credentials.
            kwargs is a dictionary of possible keywords:
                aws_access_key_id
                aws_secret_access_key
                aws_default_region
                role_arn
        '''
        node = ProfileNode(name, kwargs)
        self._creds[name] = node
    def get_profile(self, name):
        ''' Create a client for account 'name'
        '''
        node = self._creds[name]
        return node
    def __contains__(self, key):
        return key in self._creds
    def __iter__(self):
        for i in self._creds:
            yield i
