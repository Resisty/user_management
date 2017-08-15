#!/usr/bin/env python
"""Tests LDAP configuration files

Example:
    import unittest
    suite = test_userdict.suite()
    unittest.TextTestRunner().run(suite)

"""
import unittest
from jldap import userdict

NAME = 'test'
PERMISSIONS = {'key': 'value'}
USER_DICT = {'name': NAME, 'permissions': PERMISSIONS}

class UserdictTestCase(unittest.TestCase):
    ''' Test cases for jldap.userdict
    '''
    def test_constructor(self):
        ''' Test the constructor without an argument
        '''
        # pylint: disable=no-value-for-parameter
        self.assertTrue(isinstance(userdict.Userdict(), userdict.Userdict))

    def test_constructor_with_arg(self):
        ''' Test the constructor to create a Userdict object with arguments
        '''
        self.assertTrue(isinstance(userdict.Userdict(name=NAME),
                                   userdict.Userdict))

    def setUp(self):
        ''' Create a userdict.Userdict object for testing
        '''
        self.userdict = userdict.Userdict(name=NAME,
                                          permissions=PERMISSIONS)

    def test_name(self):
        ''' Test the name property
        '''
        self.assertEqual(self.userdict.name, NAME)

    def test_name_setter(self):
        ''' Test the name setter
        '''
        self.userdict.name = 'new'
        self.assertEqual(self.userdict.name, 'new')

    def test_found_blank(self):
        ''' Test the found property on a user without permissions
        '''
        temp_userdict = userdict.Userdict()
        self.assertEqual(temp_userdict.found, False)

    def test_found_with_perms(self):
        ''' Test the found property on a user with permissions
        '''
        self.assertEqual(self.userdict.found, True)

    def test_repr(self):
        ''' Test the representation of the userdict
        '''
        dict_repr = str(USER_DICT)
        self.assertEqual(repr(self.userdict), dict_repr)

    def test_str(self):
        ''' Test the stringification of the userdict
        '''
        dict_str = str(USER_DICT)
        self.assertEqual(str(self.userdict), dict_str)

    def test_dict(self):
        ''' Test the dict method of the userdict
        '''
        self.assertEqual(self.userdict.dict(), USER_DICT)

    def test_values(self):
        ''' Test the values method of the userdict
        '''
        self.assertEqual(self.userdict.values(), PERMISSIONS.values())

    def test_keys(self):
        ''' Test the keys method of the userdict
        '''
        self.assertEqual(self.userdict.keys(), PERMISSIONS.keys())

    def test_update(self):
        ''' Test the update method of the userdict
        '''
        new_dict = {'new': 'dict'}
        self.userdict.update(new_dict)
        new_dict.update(PERMISSIONS)
        self.assertEqual(self.userdict.dict(),
                         {'name': NAME, 'permissions': new_dict})

    def test_update_found(self):
        ''' Test the userdict's update method's side effect of keeping
            the found property to True when permissions are present
        '''
        new_dict = {'new': 'dict'}
        self.userdict.update(new_dict)
        self.assertEqual(self.userdict.found, True)

    def test_update_foundnotfound(self):
        ''' Test the userdict's update method's side effect of setting the
            found property to False when no permissions are present, then back
            to True when permissions are entered
        '''
        new_dict = {}
        self.userdict.update(new_dict)
        self.userdict.update({1:1})
        self.assertEqual(self.userdict.found, True)

    def test_getitem(self):
        ''' Test the __getitem__ method of the userdict
        '''
        self.assertEqual(self.userdict['key'], PERMISSIONS['key'])

    def test_setitem(self):
        ''' Test the __setitem__ method of the userdict
        '''
        self.userdict['key'] = 1
        self.assertEqual(self.userdict['key'], 1)

def suite():
    ''' Create a suite of tests
    '''
    the_suite = unittest.TestLoader().loadTestsFromTestCase(UserdictTestCase)
    return the_suite
