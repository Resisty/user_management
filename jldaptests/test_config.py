#!/usr/bin/env python
"""Tests LDAP configuration files

Example:
    import unittest
    suite = test_config.suite()
    unittest.TextTestRunner().run(suite)

"""
import unittest
import os
import yaml
from jldap import config

class ConfigTestCase(unittest.TestCase):
    ''' Test cases for jldap.config
    '''
    def test_constructor(self):
        ''' Test the constructor to fail without an argument
        '''
        # pylint: disable=no-value-for-parameter
        with self.assertRaises(TypeError):
            config.Config()

    def test_constructor_with_arg(self):
        ''' Test the constructor to create a Config object with an argument
        '''
        self.assertTrue(isinstance(config.Config('ldap_yml'), config.Config))

    def test_constructor_with_bad_arg(self):
        ''' Test the constructor to succeed with a bad argument, but result in
            an unusable object
        '''
        conf = config.Config(1)
        with self.assertRaises(TypeError):
            conf.run()

    def setUp(self):
        ''' Create a config.Config object for testing with a temporary file
        '''
        self.config_yaml = {'user': '',
                            'password': '',
                            'basedn': 'basedn',
                            'environment':
                            {'jcadev': 'jcadev',
                             'jcint': 'jcint',
                             'phx': 'phx'}}
        with open('ldap_yaml', 'w') as ldap_yaml:
            ldap_yaml.write(yaml.dump(self.config_yaml))
        self.conf = config.Config('ldap_yaml')

    def tearDown(self):
        ''' Clean up after ourselves, remove temporary config file
        '''
        os.remove('ldap_yaml')

    def test_obtained_before(self):
        ''' Test the obtained property
        '''
        self.assertFalse(self.conf.obtained)

    def test_user(self):
        ''' Test the user property
        '''
        self.assertEqual(self.conf.user, '')

    def test_obtained_after(self):
        ''' Test the obtained property after the obtain decorate is used
        '''
        _ = self.conf.user
        self.assertTrue(self.conf.obtained)

    def test_password(self):
        ''' Test the password property
        '''
        self.assertEqual(self.conf.password, '')

    def test_basedn(self):
        ''' Test the basedn property
        '''
        self.assertEqual(self.conf.basedn, 'basedn')

    def test_environments(self):
        ''' Test the environments property
        '''
        self.assertEqual(self.conf.environments,
                         self.config_yaml['environment'])

    def test_run(self):
        ''' Test the run method
        '''
        self.conf.run()
        # pylint: disable=protected-access
        self.assertEqual(self.conf._environments,
                         self.config_yaml['environment'])

def suite():
    ''' Create a suite of tests
    '''
    the_suite = unittest.TestLoader().loadTestsFromTestCase(ConfigTestCase)
    return the_suite
