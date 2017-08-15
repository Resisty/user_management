#!/usr/bin/env python
"""config module
Abstraction for LDAP configuration files

Example:
    import jldap.config
    conf = jldap.config.Config(path)


"""
import functools
import yaml

def obtain(func):
    ''' Decorator to make sure configs are obtained upon use
    '''
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        ''' The wrapper for the decorator
        '''
        if not self.obtained:
            self.run()
        return func(self, *args, **kwargs)
    return wrapper

class Config(object):
    ''' Abstraction for LDAP configuration files
    '''
    def __init__(self, cfg):
        self._configfile = cfg
        self._obtained = False
        self._user = None
        self._password = None
        self._basedn = None
        self._environments = {}
    @property
    def obtained(self):
        ''' The user for the LDAP connection
        '''
        return self._obtained
    @property
    @obtain
    def user(self):
        ''' The user for the LDAP connection
        '''
        return self._user
    @user.setter
    def user(self, usr_):
        ''' Change/update the user
        '''
        self._user = usr_
        return self._user
    @property
    @obtain
    def password(self):
        ''' The password for the user for the LDAP connection
        '''
        return self._password
    @password.setter
    def password(self, pwrd):
        ''' Change the password
        '''
        self._password = pwrd
        return self._password
    @property
    @obtain
    def basedn(self):
        ''' The base dn to search in the LDAP connection
        '''
        return self._basedn
    @basedn.setter
    def basedn(self, bsdn):
        ''' Change/update the base dn to search in the LDAP connection
        '''
        self._basedn = bsdn
        return self._basedn
    @property
    @obtain
    def environments(self):
        ''' The environments (name:fqdn) to connect to
        '''
        return self._environments
    @environments.setter
    def environments(self, envt):
        ''' Update the environments/fqdns to connect to
        '''
        self._environments.update(envt)
        return self._environments

    def run(self):
        ''' Read the configuration file and obtain values
        '''
        try:
            with open(self._configfile, 'r') as yml:
                yml_opts = yaml.load(yml)
            self._user = yml_opts['user']
            self._password = yml_opts['password']
            self._basedn = yml_opts['basedn']
            self._environments = yml_opts['environment']
            self._obtained = True
        except IOError as err:
            print 'Could not open %s for reading.' % self._configfile
            print err
            raise
        except KeyError as err:
            print 'Missing configuration option.'
            print err
            raise
