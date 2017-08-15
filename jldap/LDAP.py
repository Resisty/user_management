#!/usr/bin/env python
"""LDAP module
Example:
    import jldap.LDAP
    ldap_conn = jldap.LDAP(fqdn, user=user, password=password)


Attributes:
	BASE (str): Base dn
	USERS (str): Users dn
	PURGATORY (str): Purgatory (not-yet-enabled) users dn
	DISABLED (str): Disabled users dn

Todo:
    * Re-evaluate/test enforce_attribute
"""
import functools
import ldap
import ldap.modlist
import jldap.config
import jldap.attdict
import jldap.userdict
import jldap.profile

BASE = 'dc=example,dc=com'
USERS = 'ou=users,%s' % BASE
PURGATORY = 'ou=user-purgatory,%s' % BASE
DISABLED = 'ou=user-disabled,%s' % BASE

LDAP_MAP = {'samba-group-sid': 'sambaPrimaryGroupSID',
            'primary-gid-number': 'gidNumber',
            'employeeType': 'employeeType'}

def connect(func):
    ''' Decorator for connecting to ldap "automatically"
    '''
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        ''' The wrapper for the decorator
        '''
        prot = 'ldap://' if not self.secure else 'ldaps://'
        self.conn = ldap.initialize(prot+self.host)
        # pylint: disable=no-member
        # ldap.OPT_REFERRALS is totally a thing
        self.conn.set_option(ldap.OPT_REFERRALS, 0)
        self.conn.simple_bind_s(self.user or '', self.password or '')
        return func(self, *args, **kwargs)
    return wrapper

class LDAP(object):
    ''' Class for connecting to LDAP and making queries '''
    @classmethod
    def from_config(cls, config, env=None):
        ''' Create an ldap connection from a config file
        '''
        if env:
            envs = [config.environments[env]]
        else:
            envs = config.environments.values()
        for environ in envs:
            ldap_conn = LDAP(environ,
                             basedn=config.basedn,
                             user=config.user,
                             password=config.password)
            yield ldap_conn

    def __init__(self, host, secure=False, basedn=BASE, user=None, password=None):
        # pylint: disable=too-many-arguments
        # I need these shits
        self._host = host
        self._secure = secure
        self._basedn = basedn
        self._user = user
        self._password = password
        self._conn = None
    @property
    def host(self):
        ''' The host to connect to
        '''
        return self._host
    @property
    def secure(self):
        ''' Whether or not to use secure connection
        '''
        return self._secure
    @property
    def basedn(self):
        ''' The base dn to search down from
        '''
        return self._basedn
    @basedn.setter
    def basedn(self, bsdn):
        ''' Set/change the base dn
        '''
        self._basedn = bsdn
    @property
    def user(self):
        ''' The user to connect as
        '''
        return self._user
    @user.setter
    def user(self, usr_):
        ''' Change the user
        '''
        self._user = usr_
    @property
    def password(self):
        ''' The password for the user to connect as
        '''
        return self._password
    @password.setter
    def password(self, pwrd):
        ''' Change the password
        '''
        self._password = pwrd
    @property
    def conn(self):
        ''' The ldap connection
        '''
        return self._conn
    @conn.setter
    def conn(self, cnxn):
        ''' Change/update the ldap connection
        '''
        self._conn = cnxn
    @connect
    def search(self, basedn=None, filterstr=None, attrlist=None):
        ''' Perform an LDAP search, generating results
        '''
        base = basedn if basedn else self._basedn
        # pylint: disable=no-member
        # ldap.SCOPE_SUBTREE is totally a thing
        scope = ldap.SCOPE_SUBTREE
        args = [base, scope]
        kwargs = {'attrlist': (attrlist if attrlist else [])}
        if filterstr:
            kwargs.update({'filterstr': filterstr})
        result = self._conn.search_s(*args, **kwargs)
        for res in result:
            res[1].update({'dn': res[0]})
            yield jldap.attdict.Attdict(res[1])
    @connect
    def get_user(self, user, basedn=None, filterfield='uid'):
        ''' Searches for a user and returns the LDAP """object"""
            which is just a dict in our case
        '''
        basedn = self.basedn if not basedn else basedn
        filterstr = '(%s=%s)' % (filterfield, user)
        return self.search(basedn=basedn, filterstr=filterstr).next()
    @connect
    def get_all_uids(self):
        ''' Searches for a user and returns the LDAP """object"""
            which is just a dict in our case
        '''
        basedn = USERS
        filterstr = '(&(objectClass=person)(uid=*))'
        return [i.uid[0] for i in self.search(basedn=basedn, filterstr=filterstr)]
    @connect
    def move_user(self, uid, dest_ou, src_ou=None):
        ''' Convenience method, finds a uid in a source ou (like
            LDAP.PURGATORY) and moves it to dest_ou
        '''
        obj = self.get_user(uid, basedn=src_ou)
        if obj is None:
            return None
        self._conn.rename_s(obj.dn,
                            'uid=%s' % obj.uid[0],
                            newsuperior=dest_ou)
        return self.get_user(uid, basedn=dest_ou)
    @connect
    def user_search(self, user):
        ''' Convenience method, searches for a user's groups, unique-member
            groups, and checks to see if the user is in user-purgatory (not yet
            activated)
        '''
        attrs = ['dn']
        searches = {'memberUid':
                        {'basedn': None,
                         'filterstr': '(memberUid=%s)' % user,
                         'attrlist': attrs},
                    'user-purgatory':
                        {'basedn': PURGATORY,
                         'filterstr': '(uid=%s)' % user,
                         'attrlist': attrs},
                    'uniqueMember':
                        {'basedn': None,
                         'filterstr': '(uniqueMember=uid=%s,%s)' % (user, USERS),
                         'attrlist': attrs},
                   }
        results = jldap.userdict.Userdict(name=user)
        for key, search in searches.items():
            result = self.search(**search)
            tmplist = []
            for i in result:
                tmplist.append(i.dn)
                recursive_memberships = self._recurse_groups(i.dn)
                if recursive_memberships:
                    tmplist.append(recursive_memberships)
            results[key] = tmplist # must use assignment to trigger
                                   # userdict.__setitem__ -> set userdict.found
                                   # to True
        return results
    @connect
    def cn_search(self, common_name):
        ''' Convenience method, try to find a uid from a cn and return
            user_search(uid)
        '''
        try:
            most_likely = (self
                           .search(filterstr='(cn=%s)' % common_name)
                           .next()
                           .uid[0])
            return self.user_search(most_likely)
        except StopIteration:
            return jldap.userdict.Userdict()
    @connect
    def _recurse_groups(self, group_dn):
        ''' Method for recursively assembling group memberships
            Intended only for use in self.user_search
            Argument: group_dn should be an LDAP distinguished name (string)
        '''
        retlist = []
        for result in self.search(filterstr='(uniqueMember=%s)' % group_dn):
            retlist.append(result.dn)
            recurse_list = self._recurse_groups(result.dn)
            if recurse_list:
                retlist.append(recurse_list)
        return retlist
    @connect
    def add_object(self, obj, ignore_attrs=None):
        ''' Insert an LDAP-formatted object into a tree
            Likely from another LDAP tree
        '''
        ignore_attrs = ignore_attrs if ignore_attrs else []
        attrs = {i:j for i, j in obj.items() if i not in ignore_attrs}
        ldif = ldap.modlist.addModlist(attrs)
        self._conn.add_s(obj.dn, ldif)
        return [i for i in self.search(basedn=obj.dn)]
    @connect
    def enforce_attribute(self, attr, obj, val, replace=False):
        ''' Make sure an attribute for an object has a value. Optionally make
            the value the ONLY value for that attribute.
        '''
        result_val, is_list = ((val, True) if isinstance(val, list)
                               else ([val], False))
        if attr in obj and (val not in obj[attr]
                            or (is_list and
                                not set(val).issubset(set(obj[attr])))):
            old = {attr: obj[attr]}
            new = {attr: result_val if replace else obj[attr] + result_val}
        elif attr not in obj:
            old = {}
            new = {attr: result_val}
        else:
            return []
        ldif = ldap.modlist.modifyModlist(old, new)
        if not ldif:
            print 'No changes to attribute %s' % attr
            return []
        try:
            self._conn.modify_s(obj.dn, ldif)
        # pylint: disable=no-member
        except ldap.OBJECT_CLASS_VIOLATION as err:
            print 'Just fyi: %s' % str(err)
            return []
        return [i for i in self.search(basedn=obj.dn)]
    @connect
    def replace_attribute(self, attr, obj, val):
        ''' Convenience method, take advantage of replace parameter in
        self.enforce_attribute to replace a value in an object's attribute
        '''
        return self.enforce_attribute(attr, obj, val, replace=True)
    @connect
    def degroup_user(self, username):
        ''' Convenience method. Remove username from all groups by both
            memberUid and uniqueMember
        '''
        user = self.search(basedn=USERS, filterstr='(uid=%s)' % username)
        user = user.next()
        searches = {'memberUid': user.uid[0],
                    'uniqueMember': user.dn}
        for attr, user_attr in searches.items():
            group_objs = self.search(basedn=BASE,
                                     filterstr='(%s=%s)' % (attr, user_attr),
                                     attrlist=['dn', 'cn', attr])
            for group_obj in group_objs:
                members = ([i for i in group_obj[attr]
                            if i.lower() != user_attr.lower()])
                self.replace_attribute(attr, group_obj, members)
    @connect
    def disable_user(self, username):
        ''' Convenience method, degroups user and moves it to purgatory
        '''
        try:
            self.degroup_user(username)
            self.move_user(username, USERS, DISABLED)
        except StopIteration: # degroup_user and move_user call search which
                              # can fail to yield users if they don't exist
            print ("User %s not found in LDAP tree on host %s"
                   % (username, self.host))
    @connect
    def enforce_profile(self, username, profile, jira=None):
        ''' Convenience method, unfortunately somewhat hardcoded and specific
            against current format of profile yaml.
            Username is a string, profile is a jldap.profile.Profile()
        '''
        try:
            assert isinstance(profile, jldap.profile.Profile)
        except AssertionError:
            raise TypeError('Argument "profile" must be of type %s' %
                            jldap.profile.Profile)
        try:
            self.degroup_user(username)
        except StopIteration: # degroup_user calls search which may fail to
                              # yield users
            print ("User %s not found in LDAP tree on host %s"
                   % (username, self.host))
        user = self.search(basedn=USERS, filterstr='(uid=%s)' % username)
        user = user.next()
        samba_sid_base = '-'.join([i for i in user
                                   .sambaPrimaryGroupSID[0]
                                   .split('-')][:-1])
        samba_sid = '%s-%s' % (samba_sid_base, profile.samba_group_sid)
        self.replace_attribute('remoteAccess', user, 'TRUE')
        self.replace_attribute('sambaPrimaryGroupSID', user, samba_sid)
        self.replace_attribute('gidNumber', user, profile.primary_gid_number)
        self.replace_attribute('employeeType',
                               user,
                               'LDAP Profile: %s' % profile.name)
        if jira: # required for enablement
            new_desc = ' '.join([user.description[0], jira])
            self.replace_attribute('description', user, new_desc)
        for group in profile.posix_group:
            group_obj = self.search(basedn=group).next()
            self.enforce_attribute('uniqueMember', group_obj, user.dn)
            self.enforce_attribute('memberUid', group_obj, user.uid[0])
        for group in profile.group_of_unique_names:
            group_obj = self.search(basedn=group).next()
            self.enforce_attribute('uniqueMember', group_obj, user.dn)
        for group in profile.samba_group_mapping:
            group_obj = self.search(basedn=group).next()
            self.enforce_attribute('memberUid', group_obj, user.uid[0])
