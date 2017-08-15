#!/usr/bin/env python
"""Tests LDAP Jive

Example:
    import unittest
    suite = test_jive.suite()
    unittest.TextTestRunner().run(suite)

"""
import unittest
from collections import namedtuple
import mock
from jldap import jive

class JiveTestCase(unittest.TestCase):
    ''' Test cases for jldap.jive
    '''
    def setUp(self):
        ''' Set up for testing
        '''
        self.jive = jive.JiveApi()
    @mock.patch('jldap.jive.requests')
    def test_search(self, mock_requests):
        ''' Test the ability to search via api
        '''
        retval = namedtuple('MockGet', ['text', 'statuscode'])
        retval.text = '{"list": []}'
        retval.statuscode = 200
        mock_requests.get.return_value = retval
        self.jive.search('test_value')
        query = self.jive.url + '/search/contents?filter=search("test_value")'
        auth = self.jive.user, self.jive.password
        headers = self.jive.headers
        mock_requests.get.assert_called_with(query, auth=auth, headers=headers)

    @mock.patch('jldap.jive.requests')
    def test_post(self, mock_requests):
        ''' Test the ability to post via api
        '''
        retval = namedtuple('MockGet', ['text', 'statuscode'])
        retval.text = '{"resources": {"html": {"ref": ""}}}'
        retval.statuscode = 200
        mock_requests.post.return_value = retval
        self.jive.post('test_subject', "<p></p>")
        url = self.jive.url + '/contents'
        data = {"type": "document",
                "status": "published",
                "subject": "test_subject",
                "content": {"type": "text/html",
                            "text": "<p></p>"
                           }
               }
        jdata = jive.json.dumps(data)
        auth = self.jive.user, self.jive.password
        headers = self.jive.headers
        mock_requests.post.assert_called_with(url,
                                              data=jdata,
                                              auth=auth,
                                              headers=headers)

def suite():
    ''' Create a suite of tests
    '''
    the_suite = unittest.TestLoader().loadTestsFromTestCase(JiveTestCase)
    return the_suite
