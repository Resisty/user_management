#!/usr/bin/env python
"""Tests LDAP

Example:
    import unittest
    suite = test_jive.suite()
    unittest.TextTestRunner().run(suite)

"""
import unittest
from collections import namedtuple
import mock
from jldap import LDAP

class LDAPTestCase(unittest.TestCase):
    ''' Test cases for jldap.LDAP
        TODO: write some tests
    '''

def suite():
    ''' Create a suite of tests
    '''
    the_suite = unittest.TestLoader().loadTestsFromTestCase(LDAPTestCase)
    return the_suite
