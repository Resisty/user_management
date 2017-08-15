#!/usr/bin/env python
"""Tests LDAP Profiles

Example:
    import unittest
    suite = test_profile.suite()
    unittest.TextTestRunner().run(suite)

"""
import unittest
import os
import tempfile
import shutil
import collections
import yaml
from jldap import profile
from jldap import userdict
from jldap import config
PROFILE_NAME = 'test'
PROF_FILE = PROFILE_NAME + '.yaml'

''' PROFILE is the expected format of an LDAP profile after it has been pulled
    from YAML into a dict.
'''
PROFILE = {'group-of-unique-names': ['cn=rundeck-admin,ou=roles,ou=groups,dc=example,dc=com',
                                     'cn=pwm,ou=servicegroups,ou=groups,dc=example,dc=com',
                                     'cn=allow_all_usergroups,ou=hostaccessgroups,ou=groups,dc=example,dc=com',
                                     'cn=Directory Administrators,dc=example,dc=com',
                                     'cn=ucsadmins,ou=accessgroups,ou=groups,dc=example,dc=com',
                                     'cn=nfsmgr,ou=roles,ou=groups,dc=example,dc=com',
                                     'cn=backupmgr,ou=roles,ou=groups,dc=example,dc=com'],
           'okta-aws-roles': {'sandbox': 'Administrator'},
           'owner': 'first.last',
           'posix-group': ['cn=granted-access-to-all,ou=hostaccessgroups,ou=groups,dc=example,dc=com'],
           'primary-gid-number': 10000,
           'samba-group-mapping': ['cn=Domain Admins,ou=windows,ou=accessgroups,ou=groups,dc=example,dc=com',
                                   'cn=vCenter Admins,ou=windows,ou=accessgroups,ou=groups,dc=example,dc=com'],
           'samba-group-sid': 2000}

''' TEST_PERMISSIONS is a set of permissions as returned in a Userdict object
    from an LDAP.user_search() query.
'''
TEST_PERMISSIONS = {'memberUid': [['cn=unrestricted,ou=roles,ou=groups,dc=example,dc=com'],
                                  'cn=Domain Admins,ou=windows,ou=accessgroups,ou=groups,dc=example,dc=com',
                                  'cn=vCenter Admins,ou=windows,ou=accessgroups,ou=groups,dc=example,dc=com',
                                  'cn=docker,ou=roles,ou=groups,dc=example,dc=com'],
                    'uniqueMember': ['cn=ZenManager,ou=zenoss,ou=servicegroups,ou=groups,dc=example,dc=com',
                                     'cn=pwm,ou=servicegroups,ou=groups,dc=example,dc=com',
                                     ['cn=unrestricted,ou=roles,ou=groups,dc=example,dc=com'],
                                     'cn=allow_all_usergroups,ou=hostaccessgroups,ou=groups,dc=example,dc=com',
                                     'cn=granted-access-to-all,ou=hostaccessgroups,ou=groups,dc=example,dc=com',
                                     'cn=JuniperGuest,ou=network,ou=accessgroups,ou=groups,dc=example,dc=com',
                                     'cn=Directory Administrators,dc=example,dc=com',
                                     'cn=ucsadmins,ou=accessgroups,ou=groups,dc=example,dc=com',
                                     'cn=vcops.admins,ou=roles,ou=groups,dc=example,dc=com',
                                     'cn=backupmgr,ou=roles,ou=groups,dc=example,dc=com',
                                     'cn=nfsmgr,ou=roles,ou=groups,dc=example,dc=com',
                                     'cn=rundeck-admin,ou=roles,ou=groups,dc=example,dc=com'],
                    'user-purgatory': []}

''' DISJOINT_PERMISSIONS is a set of permissions as returned in a Userdict object
    from an LDAP.user_search() query, used for explicit audit testing because
    meaningful tests require disjoint permissions compared to the audited
    profile.
'''
DISJOINT_PERMISSIONS = {'memberUid': [['cn=unrestricted,ou=roles,ou=groups,dc=example,dc=com'],
                                      'cn=Domain Admins,ou=windows,ou=accessgroups,ou=groups,dc=example,dc=com',
                                      'cn=Nonsense Group,ou=not-exist,dc=example,dc=com',
                                      'cn=vCenter Admins,ou=windows,ou=accessgroups,ou=groups,dc=example,dc=com'],
                        'uniqueMember': ['cn=ZenManager,ou=zenoss,ou=servicegroups,ou=groups,dc=example,dc=com',
                                         'cn=pwm,ou=servicegroups,ou=groups,dc=example,dc=com',
                                         ['cn=unrestricted,ou=roles,ou=groups,dc=example,dc=com'],
                                         'cn=allow_all_usergroups,ou=hostaccessgroups,ou=groups,dc=example,dc=com',
                                         'cn=granted-access-to-all,ou=hostaccessgroups,ou=groups,dc=example,dc=com',
                                         'cn=JuniperGuest,ou=network,ou=accessgroups,ou=groups,dc=example,dc=com',
                                         'cn=Directory Administrators,dc=example,dc=com',
                                         'cn=ucsadmins,ou=accessgroups,ou=groups,dc=example,dc=com',
                                         'cn=vcops.admins,ou=roles,ou=groups,dc=example,dc=com',
                                         'cn=docker,ou=roles,ou=groups,dc=example,dc=com',
                                         'cn=backupmgr,ou=roles,ou=groups,dc=example,dc=com',
                                         'cn=nfsmgr,ou=roles,ou=groups,dc=example,dc=com',
                                         'cn=rundeck-admin,ou=roles,ou=groups,dc=example,dc=com'],
                        'user-purgatory': []}

''' TEST_USER and DISJOINT_USER are Userdicts which are used to test the
    audit() method and methods calling audit()
'''
TEST_USER = userdict.Userdict(name='flolrus', permissions=TEST_PERMISSIONS)
DISJOINT_USER = userdict.Userdict(name='flolrus', permissions=DISJOINT_PERMISSIONS)

class ProfileTestCase(unittest.TestCase):
    ''' Test cases for jldap.profile
    '''
    def setUp(self):
        ''' Set up for testing
        '''
        self.temp_profiles = tempfile.mkdtemp()
        self.empty = tempfile.mkdtemp()
        self.prof_file = os.path.join(self.temp_profiles, PROF_FILE)
        with open(self.prof_file, 'w') as prof:
            prof.write(yaml.dump(PROFILE))
    def tearDown(self):
        ''' Clean up after ourselves
        '''
        shutil.rmtree(self.temp_profiles)
    def test_constructor(self):
        ''' Test that the constructor fails without an argument
        '''
        # pylint: disable=no-value-for-parameter
        with self.assertRaises(TypeError):
            profile.Profile()
    def test_constructor_with_arg(self):
        ''' Test the constructor to create a Profile object with an argument
        '''
        self.assertTrue(isinstance(profile.Profile(self.prof_file),
                                   profile.Profile))
    def test_constructor_with_bad_arg(self):
        ''' Test the constructor to fail when given an incorrect argument
        '''
        with self.assertRaises(AttributeError):
            profile.Profile(1)
    def test_constructor_with_wrong_arg(self):
        ''' Test that the constructor succeeds with an argument of the correct
            type but doesn't exist
        '''
        # pylint: disable=no-value-for-parameter
        with self.assertRaises(IOError):
            prof = profile.Profile(os.path.join(self.temp_profiles,
                                                'nonexistent.yaml'))
            prof.run()
    def test_from_directory_good_arg(self):
        ''' Test from_directory class method with a existent, profile-full
            directory
        '''
        profiles = profile.Profile.from_directory(self.temp_profiles)
        self.assertTrue(isinstance(profiles.next(), profile.Profile))
    def test_from_directory_bad_arg(self):
        ''' Test from_directory class method with a nonexistent or empty
            directory
        '''
        profiles = profile.Profile.from_directory(self.empty)
        with self.assertRaises(StopIteration):
            profiles.next()
    def test_bulk_audit_path(self):
        ''' Test bulk_audit class method with the path keyword
        '''
        audit = profile.Profile.bulk_audit(TEST_USER, path=self.temp_profiles)
        # testing the actual audit and whether or not a user has the
        # permissions it needs is currently beyond the scope of this project
        self.assertTrue(isinstance(audit, collections.OrderedDict))
    def test_bulk_audit_profiles(self):
        ''' Test bulk_audit class method with the profiles keyword
        '''
        prof = profile.Profile(self.prof_file)
        audit = profile.Profile.bulk_audit(TEST_USER, profiles=[prof])
        self.assertTrue(isinstance(audit, collections.OrderedDict))
    def test_bulk_audit_no_profiles(self):
        ''' Test that the bulk_audit class method fails when it is not given
            profiles
        '''
        with self.assertRaises(TypeError):
            profile.Profile.bulk_audit(TEST_USER)
    def test_bulk_audit_ignore_inherit(self):
        ''' Test that the bulk_audit class method returns returns different
            results when ignore_inherited is set to True vs False
            This assumes there are nested groups in the LDAP directory!
        '''
        prof = profile.Profile(self.prof_file)
        inherit_audit = profile.Profile.bulk_audit(TEST_USER, profiles=[prof])
        no_inherit_audit = profile.Profile.bulk_audit(TEST_USER,
                                                      profiles=[prof],
                                                      ignore_inherited=True)
        self.assertFalse(inherit_audit == no_inherit_audit)
    def test_bulk_audit_explicit(self):
        ''' Test that the bulk_audit class method returns returns different
            results when explicit is set to True vs False
            Requires a user with disjoint memberships with respect to the
            profile!
        '''
        prof = profile.Profile(self.prof_file)
        audit = profile.Profile.bulk_audit(DISJOINT_USER, profiles=[prof])
        explicit_audit = profile.Profile.bulk_audit(DISJOINT_USER,
                                                      profiles=[prof],
                                                      ignore_inherited=True)
        self.assertFalse(audit == explicit_audit)
    def test_name(self):
        ''' Test name property
        '''
        prof = profile.Profile(self.prof_file)
        self.assertEquals(PROF_FILE, prof.name)
    def test_samba_group_sid(self):
        ''' Test samba_group_sid property
        '''
        prof = profile.Profile(self.prof_file)
        self.assertEquals(str(PROFILE['samba-group-sid']), prof.samba_group_sid)
    def test_primary_gid_number(self):
        ''' Test primary_gid_number property
        '''
        prof = profile.Profile(self.prof_file)
        # attributes are strings because LDAP
        self.assertEquals(str(PROFILE['primary-gid-number']), prof.primary_gid_number)
    def test_posix_group(self):
        ''' Test posix_group property
        '''
        prof = profile.Profile(self.prof_file)
        self.assertEquals(PROFILE['posix-group'], prof.posix_group)
    def test_group_of_unique_names(self):
        ''' Test group_of_unique_names property
        '''
        prof = profile.Profile(self.prof_file)
        self.assertEquals(PROFILE['group-of-unique-names'], prof.group_of_unique_names)
    def test_samba_group_mapping(self):
        ''' Test amba_group_mapping property
        '''
        prof = profile.Profile(self.prof_file)
        self.assertEquals(PROFILE['samba-group-mapping'],
                          prof.samba_group_mapping)
    def test_keys(self):
        ''' Test keys method
        '''
        prof = profile.Profile(self.prof_file)
        self.assertEquals(sorted(PROFILE.keys()),
                          sorted(prof.keys()))
    def test_values(self):
        ''' Test values method
        '''
        prof = profile.Profile(self.prof_file)
        self.assertEquals(sorted(PROFILE.values()),
                          sorted(prof.values()))
    def test_getitem(self):
        ''' Test __getitem__ method
        '''
        prof = profile.Profile(self.prof_file)
        self.assertEquals(PROFILE['owner'],
                          prof['owner'])

def suite():
    ''' Create a suite of tests
    '''
    the_suite = unittest.TestLoader().loadTestsFromTestCase(ProfileTestCase)
    return the_suite
