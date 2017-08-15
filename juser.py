#!/usr/bin/env python
"""juser module / script
Example:
    $ python juser.py search username

Attributes:
	LDAP_YML (str): Default location of LDAP connection configuration
            file. Requires environment FQDNs and bind user/password.
        PROFILE_DIR (str): Default location of profile yaml files.

"""
import argparse
import os

from jldap import functions

LDAP_YML = os.path.expanduser('~/.ldap.yml')
PROFILE_DIR = os.path.expanduser('./profiles')

def main():
    """ Target of execution entry
    """
    parser = argparse.ArgumentParser(description='Perform a user search \
against LDAP')
    parser.add_argument('-c', '--config',
                        default=LDAP_YML,
                        help='YAML file containing LDAP configuration. \
Default location: %s' % LDAP_YML)
    parser.add_argument('-e', '--environment',
                        default='phx',
                        help='LDAP environment (host) to use in connection(s).')
    subparsers = parser.add_subparsers(dest='subparser_name')

    search_parser = subparsers.add_parser('search')
    search_parser.add_argument('user',
                               help='User for whom to search LDAP')
    search_parser.add_argument('-c', '--common_name',
                               action='store_true',
                               help='Search by common name')
    search_parser.add_argument('-r', '--raw',
                               action='store_true',
                               help='Return raw LDAP object')
    search_parser.set_defaults(func=functions.usersearch)

    enable_parser = subparsers.add_parser('enable')
    enable_parser.add_argument('user',
                               help='User to enable in LDAP')
    enable_parser.add_argument('profile',
                               help='Name of the profile to assign to user',
                               type=functions.prof_file)
    enable_parser.add_argument('jira',
                               help='JIRA number requesting and approving user \
enablement')
    enable_parser.add_argument('-p', '--profile_dir',
                               default=PROFILE_DIR,
                               help='Directory in which profiles reside')
    enable_parser.set_defaults(func=functions.userenable)

    move_parser = subparsers.add_parser('move')
    move_parser.add_argument('user',
                             help='User to enable in LDAP')
    move_parser.add_argument('profile',
                             help='Name of the profile to assign to user',
                             type=functions.prof_file)
    move_parser.add_argument('-p', '--profile_dir',
                             default=PROFILE_DIR,
                             help='Directory in which profiles reside')
    move_parser.set_defaults(func=functions.useradjust)

    disable_parser = subparsers.add_parser('disable')
    disable_parser.add_argument('user',
                                help='User to disable in LDAP')
    disable_parser.set_defaults(func=functions.userdisable)

    audit_parser = subparsers.add_parser('audit')
    audit_parser.add_argument('-p', '--profile_dir',
                              default=PROFILE_DIR,
                              help='Directory in which profiles reside')
    audit_parser.add_argument('-u', '--users',
                              type=str,
                              nargs='*',
                              help='User(s) to audit')
    audit_parser.add_argument('-x', '--html',
                              default=False,
                              action='store_true',
                              help='Output audit information in HTML format')
    audit_parser.add_argument('-i', '--ignore',
                              default=False,
                              action='store_true',
                              help='Ignore inherited permissions (e.g. parent \
groups)')
    audit_parser.add_argument('-e', '--explicit',
                              default=False,
                              action='store_true',
                              help='Use explicit audits per profile (include \
name and diff even if no match)')
    audit_parser.set_defaults(func=functions.audit)

    explicit_audit_parser = subparsers.add_parser('explicit_audit')
    explicit_audit_parser.add_argument('profile',
                                       help='Name of profile to audit',
                                       type=functions.prof_file)
    explicit_audit_parser.add_argument('-p', '--profile_dir',
                                       default=PROFILE_DIR,
                                       help='Path to profile yaml')
    explicit_audit_parser.add_argument('-u', '--users',
                                       type=str,
                                       nargs='*',
                                       help='User(s) to audit')
    explicit_audit_parser.add_argument('-x', '--html',
                                       default=False,
                                       action='store_true',
                                       help='Output audit information in HTML \
format')
    explicit_audit_parser.add_argument('-i', '--ignore',
                                       default=False,
                                       action='store_true',
                                       help='Ignore inherited permissions (e.g. parent \
groups)')
    explicit_audit_parser.set_defaults(func=functions.explicit_audit)

    profiles_parser = subparsers.add_parser('profiles')
    profiles_parser.add_argument('-p', '--profile_dir',
                                 default=PROFILE_DIR,
                                 help='Path to profile yaml')
    profiles_parser.add_argument('-s', '--single',
                                 type=functions.profile_suf,
                                 help='Display specific profile by name')
    profiles_parser.set_defaults(func=functions.profile_dumper)

    pubkey_parser = subparsers.add_parser('pubkey')
    pubkey_parser.add_argument('user',
                               help='User for whom to propagate pubkey across LDAP')
    pubkey_parser.add_argument('-e', '--environment',
                               help='Source environment from which to obtain \
pubkey. Default: phx',
                               default='phx')
    pubkey_parser.set_defaults(func=functions.propagate_pubkeys)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
