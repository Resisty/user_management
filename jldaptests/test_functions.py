#!/usr/bin/env python
"""Tests LDAP functions

Example:
    import unittest
    suite = test_jive.suite()
    unittest.TextTestRunner().run(suite)

"""
import unittest
from collections import namedtuple
import mock
from jldap import functions

class FunctionsTestCase(unittest.TestCase):
    ''' Test cases for jldap.functions
        TODO: write some tests
    '''

def suite():
    ''' Create a suite of tests
    '''
    the_suite = unittest.TestLoader().loadTestsFromTestCase(FunctionsTestCase)
    return the_suite
