#!/usr/bin/env python
''' Main module, basically a script
'''
import os
import argparse
import pprint
import regex
import okta.client as client

CFGYML = os.path.join(os.path.dirname(__file__), 'key.yml')

def apps_by_user(args):
    ''' Default function for userapps parser.
        Gets applications per user from Okta client(s)
    '''
    users = args.users
    uclient = client.UserClient.from_config(args.config_file)
    aclient = client.AppClient.from_config(args.config_file)
    uids = {}
    for user in users:
        uids[uclient.get_user_by_email(user).id] = user
    user_apps = aclient.get_apps_by_user(uids.keys())
    for uid, apps in user_apps.items():
        print 'User: %s' % uids[uid]
        print 'Apps:'
        for app in apps:
            if not regex.match(args.filter,
                               app.label,
                               {True: regex.I,
                                False: 0}[args.sensitive]):
                continue
            appinfo = aclient.get_user_from_app(app, uid)
            try:
                role = appinfo.profile['role']
            except KeyError:
                print('No "role" in appinfo.profile. Appinfo: %s' % appinfo)
                continue
            samlrole = ', '.join(appinfo.profile['samlRoles'])
            print ('%s:\n\tRole:%s\n\tSamlRoles:%s'
                   % (app.label, role, samlrole))
        print

def users_by_app(args):
    ''' Default function for appusers parser.
        Gets users per application from Okta client(s)
    '''
    aclient = client.AppClient.from_config(args.config_file)
    apps = aclient.get_apps_by_label(args.app)
    for app in apps:
        appusers = aclient.get_user_from_app(app)
        print 'Users for application "%s"' % app.label
        for user in appusers:
            if 'firstName' not in user.profile or user.profile['firstName'] is None:
                print 'Misconfigured user? %s' % pprint.pformat(user)
            else:
                print ('%s %s, %s'
                       % (user.profile['firstName'],
                          user.profile['lastName'],
                          user.profile['email']))
                print '\tRole: %s' % user.profile['role']
                print '\tSAMLRoles: %s' % ', '.join(user.profile['samlRoles'])

def main():
    ''' Main function. Entry point.
    '''
    parser = argparse.ArgumentParser('Do Okta API stuff')
    parser.add_argument('-c', '--config_file',
                        help='Path to config yaml',
                        default=CFGYML)
    subparsers = parser.add_subparsers(dest='subparser_name')
    userapps = subparsers.add_parser('userapps',
                                     help='Get apps by user email')
    userapps.add_argument('users',
                          nargs='+',
                          type=str)
    userapps.add_argument('-f', '--filter',
                          help='Substring which app results should match \
                          against',
                          type=str,
                          default='')
    userapps.add_argument('-s', '--sensitive',
                          help='If present, indicates --filter should be \
                          case-sensitive.',
                          action='store_false',
                          default=True)
    userapps.set_defaults(func=apps_by_user)

    appusers = subparsers.add_parser('appusers',
                                     help='Get users by app substring')
    appusers.add_argument('app',
                          help='Case-insensitive substring to match against \
application labels',
                          type=str)
    appusers.set_defaults(func=users_by_app)
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
