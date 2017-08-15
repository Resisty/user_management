#!/usr/bin/env python
"""jaws module / script
Example:
    $ python jawshelper.py search username

Attributes:
	LDAP_YML (str): Default location of LDAP connection configuration
	file. Requires environment FQDNs and bind user/password.

"""
import argparse
import os
import re
from jaws import client

AWS_CREDS = os.path.expanduser('~/.aws/credentials')

def aws_users(args):
    ''' Perform a search against configured accounts in ~/.aws/credentials.
    '''
    creds = client.Credentials.from_file(args.config)
    for prof in creds:
        iam = creds.get_profile(prof).get_client()
        try:
            user = iam.get_user(UserName=args.user)
            print 'Found %s in account %s' % (user['User']['UserName'], prof)
        except client.botocore.exceptions.ClientError:
            print '%s not in account %s' % (args.user, prof)

def main():
    """ Target of execution entry
    """
    parser = argparse.ArgumentParser(description='Perform a user search \
against AWS accounts')
    parser.add_argument('-c', '--config',
                        default=AWS_CREDS,
                        help='File containing AWS credentials. \
Default location: %s' % AWS_CREDS)
    subparsers = parser.add_subparsers(dest='subparser_name')

    aws_users_parser = subparsers.add_parser('aws_users')
    aws_users_parser.add_argument('user',
                                  help='User to search for in AWS accounts')
    aws_users_parser.set_defaults(func=aws_users)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
