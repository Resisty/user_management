#!/usr/bin/env python
"""profile module
Example:
    import jldap.profile
    prof = jldap.profile.Profile(path)


Attributes:
	PATTERN (str): Default pattern to match profile files against
	PROFILE_KEYS (list): List of keys in profile (yaml) dict
	AUDIT_DICT (collections.OrderedDict): Order-dependent dictionary of
            results from auditing a user against a Profile
"""
import functools
import re
import os
from collections import OrderedDict
import yaml
from bs4 import BeautifulSoup

PATTERN = r'\.yaml'
PROFILE_KEYS = ['samba-group-sid',
                'primary-gid-number',
                'owner',
                'posix-group',
                'group-of-unique-names',
                'samba-group-mapping']
AUDIT_DICT = OrderedDict.fromkeys(['user',
                                   'name',
                                   'text',
                                   'diff',
                                   'value'], '')
AUDIT_DICT['diff'] = []
AUDIT_DICT['value'] = 0

def obtain(func):
    ''' Decorator to obtain Profile information when needed
    '''
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        ''' The wrapper for the decorator
        '''
        if not self.obtained:
            self.run()
        return func(self, *args, **kwargs)
    return wrapper

# pylint: disable=too-many-locals
def audits2html(audits):
    ''' Takes a dict of profile_name:audit_list and converts to an html table
    '''
    soup = BeautifulSoup('', 'html5lib')
    table = soup.new_tag('table')
    table.attrs = {'style': 'border: 1px solid; border-width: 1px; border-color: #000000;'}
    soup.append(table)

    tbody = soup.new_tag('tbody')
    table.append(tbody)
    for name, audit_list in audits.items():
        # Insert "heading" for profile name
        table_row = soup.new_tag('tr')
        table_row.attrs = {'style': 'background-color: #88bbff;'}
        table_div = soup.new_tag('td')
        table_div.attrs = {'colspan': '%s' % len(audit_list[0])}
        table_div.string = ('Profile: %s, Owner: %s'
                            % (name, audit_list[0].pop('owner')))
        table_row.append(table_div)
        tbody.append(table_row)
        # Insert "heading" for notes
        table_row = soup.new_tag('tr')
        table_row.attrs = {'style': 'background-color: #dbdbdb;'}
        table_div = soup.new_tag('td')
        table_div.attrs = {'colspan': '%s' % len(audit_list[0])}
        table_div.string = 'Notes/Changes Required'
        table_row.append(table_div)
        tbody.append(table_row)
        # Insert row for notes
        table_row = soup.new_tag('tr')
        table_div = soup.new_tag('td')
        table_div.attrs = {'colspan': '%s' % len(audit_list[0])}
        table_div.string = '-'
        table_row.append(table_div)
        tbody.append(table_row)
        # Insert heading for keys. User, text, diff, etc
        table_row = soup.new_tag('tr')
        table_row.attrs = {'style': 'background-color: #dbdbdb;'}
        keys = audit_list[0].keys()[:-1] # we don't care about value at this point
        for key in keys:
            table_div = soup.new_tag('td')
            table_div.string = key
            table_row.append(table_div)
        tbody.append(table_row)
        # Insert each audit
        for audit in audit_list:
            table_row = soup.new_tag('tr')
            tbody.append(table_row)
            for key in keys:
                table_div = soup.new_tag('td')
                table_row.append(table_div)
                pre = soup.new_tag('pre')
                table_div.append(pre)
                yml_stable_rowing = yaml.dump(audit[key], default_flow_style=False)
                for line in yml_stable_rowing.split('\n'):
                    # shitty hack because yaml.dump() serializes simple stable_rowings
                    # with an extable_rowa '\n...\n'
                    if not line == '...':
                        paragraph = soup.new_tag('p')
                        paragraph.string = line
                        pre.append(paragraph)
    return str(soup)

class Profile(object):
    ''' Abstraction of profile yaml files, provides ability to audit an LDAP
        user's membership against that profile(s)
    '''
    # pylint: disable=too-many-instance-attributes
    # I need all these shits
    def __init__(self, prof):
        self._name = os.path.split(prof)[-1]
        self._prof_file = prof
        self._prof_dict = {}
        self._obtained = False
        self._samba_group_sid = None
        self._primary_gid_number = None
        self._owner = None
        self._posix_group = []
        self._group_of_unique_names = []
        self._samba_group_mapping = []

    @classmethod
    def from_directory(cls, path, pattern=PATTERN):
        ''' Generator profiles from a directory path based on a given filename
            pattern
        '''
        for _, _, files in os.walk(path):
            for filename in files:
                fullpath = os.path.join(path, filename)
                if (re.search(pattern, filename)
                        and not os.path.islink(fullpath)):
                    yield cls(fullpath)

    #pylint: disable=too-many-arguments
    @classmethod
    def bulk_audit(cls,
                   user,
                   pattern=PATTERN,
                   profiles=None,
                   path=None,
                   ignore_inherited=False,
                   explicit=False):
        ''' Generates audits for each profile in path or profiles against user.
            user argument is an LDAP.LDAP.user_search() result which is a
            userdict.Userdict()
            Keyword arguments:
                pattern: a regex pattern against which to match (and therefore
                    limit) profile filenames
                profiles: a list of profile names to audit
                path: a path to the directory containing profiles. Subordinate
                    to profiles keyword.
                ignore_inherited: If set to True, ignores inherited
                    permissions, e.g., membership in a group which is a parent
                    of a group in the profile
        '''
        audits = []
        if not profiles and not path:
            raise TypeError('Keyword arguments must include either path or \
            profiles')
        elif not profiles:
            profiles = [prof for prof in cls.from_directory(path, pattern)]
        for prof in profiles:
            audit = prof.audit(user,
                               ignore_inherited=ignore_inherited,
                               explicit=explicit)
            audits.append(audit)
        max_val = max([i['value'] for i in audits])
        remain = [a for a in audits if a['value'] == max_val]
        if not remain:
            return audits[0]
        return min(remain, key=lambda x: len(x['diff']))

    @property
    def obtained(self):
        ''' Whether or not the profile has been read/loaded
        '''
        return self._obtained
    @property
    def name(self):
        ''' The name of the profile
        '''
        return self._name
    @property
    def owner(self):
        ''' The owner of the profile
        '''
        return self._owner
    @property
    @obtain
    def samba_group_sid(self):
        ''' The samba-group-sid
        '''
        return self._samba_group_sid
    @property
    @obtain
    def primary_gid_number(self):
        ''' The primary gid number
        '''
        return self._primary_gid_number
    @property
    @obtain
    def posix_group(self):
        ''' The posix-group, list of groups to which to a user in this profile
            belongs as a memberUid
        '''
        return self._posix_group
    @property
    @obtain
    def group_of_unique_names(self):
        ''' The group-of-unique-names, another list of groups to which a user
            in this profile belongs as a uniqueMember
        '''
        return self._group_of_unique_names
    @property
    @obtain
    def samba_group_mapping(self):
        ''' The samba-group-mapping, allows LDAP resolution in Windowsland
        '''
        return self._samba_group_mapping
    @obtain
    def keys(self):
        ''' Return underlying dictionary keys
        '''
        return self._prof_dict.keys()
    @obtain
    def values(self):
        ''' Return underlying dictionary values
        '''
        return self._prof_dict.values()
    @obtain
    def __getitem__(self, key):
        return self._prof_dict[key]

    def run(self):
        ''' Read the profile and obtain the values
        '''
        with open(self._prof_file, 'r') as yml:
            self._prof_dict = yaml.load(yml)
        for i in PROFILE_KEYS:
            try:
                attr = '_' + i.replace('-', '_')
                val = self._prof_dict[i]
                val = str(val) if isinstance(val, int) else val
                setattr(self, attr, (val if val else []))
            except KeyError:
                continue
        self._obtained = True

    @obtain
    def __str__(self):
        return yaml.dump(self._prof_dict, default_flow_style=False)

    @obtain
    def audit(self, user, explicit=False, ignore_inherited=False):
        ''' User must be an LDAP.user_search(user) result
            Keyword Arguments:
                explicit: If set to True, enumerates differences for disjoint
                    permissions between user and profile
                ignore_inherited: If set to True, ignores inherited
                    permissions, e.g., membership in a group which is a parent
                    of a group in the profile
        '''
        def flatten(items, seqtypes=(list, tuple)):
            ''' Flatten permissions so we can turn into set
            '''
            for i, _ in enumerate(items):
                while i < len(items) and isinstance(items[i], seqtypes):
                    items[i:i+1] = items[i] # slice assignment is magic
            return items
        if ignore_inherited:
            user_perms = set([perm for val in user.values()
                              for perm in val
                              if not isinstance(perm, list)])
        else:
            user_perms = set(flatten(user.values()))
        profile_perms = set(self.posix_group +
                            self.group_of_unique_names +
                            self.samba_group_mapping)
        audict = OrderedDict()
        for key, val in AUDIT_DICT.items():
            audict[key] = val
        audict['name'] = self.name
        audict['owner'] = self.owner
        audict['user'] = user.name
        if not user.found:
            audict['text'] = 'User not found in LDAP.'
            audict['value'] = 4
        elif user_perms == profile_perms:
            audict['text'] = 'Profile match'
            audict['value'] = 3
        elif user_perms.issubset(profile_perms):
            audict['text'] = 'Missing permissions'
            audict['diff'] = list(profile_perms - user_perms)
            audict['value'] = 2
        elif profile_perms.issubset(user_perms):
            audict['text'] = 'Extra permissions'
            audict['diff'] = list(user_perms - profile_perms)
            audict['value'] = 2
        else:
            audict['text'] = 'Cannot match to profile'
            audict['name'] = 'N/A' if not explicit else self.name
            audict['value'] = 1
            if explicit:
                audict['diff'] = {}
                audict['diff']['extra'] = list(user_perms - profile_perms)
                audict['diff']['missing'] = list(profile_perms - user_perms)
        return audict
