#!/usr/bin/env python
"""Tests LDAP Attdict

Example:
    import unittest
    suite = test_attdict.suite()
    unittest.TextTestRunner().run(suite)

"""
import unittest
from jldap import attdict

class AttdictTestCase(unittest.TestCase):
    ''' Test cases for jldap.attdict
    '''
    def setUp(self):
        self.dict = {'a': 1, 'b': 2, 'c': 3}
        self.attdict = attdict.Attdict(self.dict)
    def test_constructor(self):
        ''' Test the constructor without an argument
        '''
        # pylint: disable=no-value-for-parameter
        self.assertTrue(isinstance(attdict.Attdict(), dict))
    def test_constructor_with_arg(self):
        ''' Test the constructor to create an Attdict object with an argument
        '''
        self.assertTrue(isinstance(attdict.Attdict(self.dict), dict))
    def test_constructor_with_bad_arg(self):
        ''' Test the constructor to fail when given an incorrect argument
        '''
        with self.assertRaises(TypeError):
            attdict.Attdict(1)
    def test_get(self):
        ''' Test __getattr__ == dict.__getitem__
        '''
        self.assertEquals(self.attdict.a, self.dict['a'])
    def test_set(self):
        ''' Test __setattr__ == dict.__setitem__
        '''
        self.attdict.q = 17
        self.assertEquals(self.attdict['q'], 17)
    def test_del(self):
        ''' Test __delattr__ == dict.__delitem__
        '''
        del self.attdict.a
        self.dict.pop('a')
        self.assertEquals(self.attdict, self.dict)

def suite():
    ''' Create a suite of tests
    '''
    the_suite = unittest.TestLoader().loadTestsFromTestCase(AttdictTestCase)
    return the_suite
