#!/usr/bin/env python
"""userdict module
Convenience class for abstracting LDAP.user_search results.

Example:
    import jldap.LDAP
    import jldap.userdict
    result = ldap_conn.search(**search_dict)
    results = jldap.userdict.Userdict(name=user)
    results[ldap_conn.host] = [i.dn for i in result]

Todo:
    * Make initialization not suck
"""
class Userdict(object):
    ''' Abstraction of an LDAP.user_search result
    '''
    def __init__(self, name='', permissions=None):
        self._name = name
        self._permissions = ({i:j for i, j in permissions.items()}
                             if permissions
                             else {})
        self._found = True if permissions else False
    @property
    def name(self):
        ''' The name of the user that was searched
        '''
        return self._name
    @name.setter
    def name(self, username):
        ''' Change/update the name
        '''
        self._name = username
    @property
    def found(self):
        ''' Whether the user was found in LDAP
        '''
        return self._found
    @found.setter
    def found(self, foundit):
        ''' Explicity set whether the user was found in LDAP
            Useful in situations wherein the user exists but has no
            permissions, so LDAP returns an empty search
        '''
        self._found = foundit
    def __repr__(self):
        ''' Representation of the object
        '''
        rep = {'name': self.name,
               'permissions': self._permissions}
        return str(rep)
    def __str__(self):
        ''' Stringification of the object
        '''
        return self.__repr__()
    def dict(self):
        ''' Dict version of the object
        '''
        dict_repr = {'name': self.name,
                     'permissions': self._permissions}
        return dict_repr
    def values(self):
        ''' Values from internal dictionary
        '''
        return self._permissions.values()
    def keys(self):
        ''' Keys from internal dictionary
        '''
        return self._permissions.keys()
    def update(self, dictionary):
        ''' Update internal dictionary
            Update found status once internal dictionary has data
        '''
        self._permissions.update(dictionary)
        self._found = True
    def __getitem__(self, k):
        ''' Mock dictionary behavior
        '''
        return self._permissions[k]
    def __setitem__(self, key, val):
        ''' Mock dictionary behavior
            Update found status when we assign permissions (even if they're
            empty)
        '''
        self._permissions[key] = val
        self._found = self._found or bool(val)
    def __delitem__(self, key):
        ''' Mock dictionary behavior
        '''
        return self._permissions.pop(key)
