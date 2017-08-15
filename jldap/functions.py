#!/usr/bin/env python
"""jldap.functions module
Example:
    import argparse
    import functions
    parser=argparse.ArgumentParser()
    parser.add_argument('-x')
    parser.set_defaults(func=functions.func)
    args=parser.parse_args()
    args.func(args)

Attributes:
    LDAP_USER (str): Env var for LDAP connections, if it exists
    LDAP_PASS (str): Env var for LDAP connections, if it exists
"""

import re
import os
from collections import defaultdict
import yaml
from jldap import config, LDAP, profile

LDAP_USER = os.environ.get('LDAP_USER')
LDAP_PASS = os.environ.get('LDAP_PASS')

def prof_file(prof):
    ''' Shim to provide file extension if only a profile name is given
    '''
    if not re.search(r'\.ya?ml', prof):
        prof += '.yaml'
    return prof

def ldap_creds(configs):
    ''' Try our best to have LDAP credentials from either a configs object or
        from environment variables
    '''
    ldap_user = configs.user if configs.user else LDAP_USER
    ldap_password = configs.password if configs.password else LDAP_PASS
    return ldap_user, ldap_password

def usersearch(args):
    """ Perform a user search against LDAP
    """
    configs = config.Config(args.config)
    results = {}
    for ldap_conn in LDAP.LDAP.from_config(configs, env=args.environment):
        if args.raw:
            if args.common_name:
                result = ldap_conn.get_user(args.user, filterfield='cn')
            else:
                result = ldap_conn.get_user(args.user)
        else:
            if args.common_name:
                result = ldap_conn.cn_search(args.user)
            else:
                result = ldap_conn.user_search(args.user)
            result = (result.dict()
                      if result.found
                      else '%s not found' % args.user)
        results[ldap_conn.host] = result
    print yaml.dump(results, default_flow_style=False)

def userenable(args):
    """ Enable a user; move user out of purgatory at a minimum.
    """
    configs = config.Config(args.config)
    ldap_user, ldap_password = ldap_creds(configs)
    prof = args.profile_dir + '/%s' % args.profile
    prof = profile.Profile(prof)
    host = configs.environments.pop(args.environment)
    origin_ldap = LDAP.LDAP(host,
                            user=ldap_user,
                            password=ldap_password,
                            basedn=configs.basedn)
    user_obj = origin_ldap.get_user(args.user)
    if not user_obj:
        raise RuntimeError('%s not found. Please contact PLOPS.' % args.user)
    origin_ldap.move_user(args.user, LDAP.USERS)
    user = origin_ldap.user_search(args.user)
    diff = prof.audit(user, explicit=True, ignore_inherited=True)
    if not 'profile match' in diff['text'].lower():
        print 'Permissions to be changed via "%s" profile:' % prof.name
        if isinstance(diff['diff'], list):
            print diff['text']
        print yaml.dump(diff['diff'], default_flow_style=False)
    origin_ldap.enforce_profile(args.user, prof, args.jira)
    user_obj = origin_ldap.get_user(args.user, LDAP.USERS)
    for _, host in configs.environments.items():
        next_ldap = LDAP.LDAP(host,
                              user=ldap_user,
                              password=ldap_password,
                              basedn=configs.basedn)
        next_user_obj = next_ldap.get_user(args.user)
        if not next_user_obj:
            next_ldap.add_object(user_obj, ignore_attrs=['dn'])
            modded_user = next_ldap.user_search(args.user)
            if not modded_user:
                raise RuntimeError('Adding user object to tree %s failed. \
Please contact PLOPS.' % next_ldap.host)
            print yaml.dump(modded_user, default_flow_style=False)
            return
        next_ldap.move_user(args.user, LDAP.USERS)
        next_user = next_ldap.user_search(args.user)
        diff = prof.audit(next_user, explicit=True, ignore_inherited=True)
        if not 'profile match' in diff['text'].lower():
            print 'Permissions to be changed via "%s" profile:' % prof.name
            if isinstance(diff['diff'], list):
                print diff['text']
            print yaml.dump(diff['diff'], default_flow_style=False)
        next_ldap.enforce_profile(args.user, prof, args.jira)
        modded_user = next_ldap.user_search(args.user)
        if modded_user:
            print yaml.dump(modded_user, default_flow_style=False)

def useradjust(args):
    """ Give a user a new profile on all environments
    """
    configs = config.Config(args.config)
    ldap_user, ldap_password = ldap_creds(configs)
    prof = args.profile_dir + '/%s' % args.profile
    prof = profile.Profile(prof)
    env = configs.environments.pop(args.environment)
    origin_ldap = LDAP.LDAP(env,
                            user=ldap_user,
                            password=ldap_password,
                            basedn=configs.basedn)
    user_obj = origin_ldap.get_user(args.user, LDAP.USERS)
    user = origin_ldap.user_search(args.user)
    diff = prof.audit(user, explicit=True, ignore_inherited=True)
    if not 'profile match' in diff['text'].lower():
        print 'Permissions to be changed via "%s" profile:' % prof.name
        if isinstance(diff['diff'], list):
            print diff['text']
        print yaml.dump(diff['diff'], default_flow_style=False)
    origin_ldap.enforce_profile(args.user, prof)
    for _, host in configs.environments.items():
        next_ldap = LDAP.LDAP(host,
                              user=ldap_user,
                              password=ldap_password,
                              basedn=configs.basedn)
        next_user = next_ldap.user_search(args.user)
        if not next_user.found:
            print ('User %s not found on %s. Full dict: "%s"'
                   % (args.user, next_ldap.host, next_user))
            try:
                next_ldap.add_object(user_obj, ignore_attrs=['dn'])
            # pylint: disable=no-member
            except LDAP.ldap.ALREADY_EXISTS: # definitely exists
                print ('User %s already exists on %s but is also "not found"???'
                       % (args.user, next_ldap.host))
            next_user = next_ldap.user_search(args.user)
        diff = prof.audit(next_user, explicit=True, ignore_inherited=True)
        if not 'profile match' in diff['text'].lower():
            print 'Permissions to be changed via "%s" profile:' % prof.name
            if isinstance(diff['diff'], list):
                print diff['text']
            print yaml.dump(diff['diff'], default_flow_style=False)
        next_ldap.enforce_profile(args.user, prof)

def userdisable(args):
    """ Disable a user; move user into purgatory at a minimum.
    """
    configs = config.Config(args.config)
    ldap_user, ldap_password = ldap_creds(configs)
    for _, host in configs.environments.items():
        print "Working on ldap host %s" % host
        next_ldap = LDAP.LDAP(host,
                              user=ldap_user,
                              password=ldap_password,
                              basedn=configs.basedn)
        next_ldap.disable_user(args.user)
        modded_user = next_ldap.user_search(args.user)
        if modded_user:
            print yaml.dump(modded_user, default_flow_style=False)

def explicit_audit(args):
    ''' Perform an LDAP audit. Find all users, evaluate how well they match to
        profiles, and generate a report.
    '''
    configs = config.Config(args.config)
    ldap_user, ldap_password = ldap_creds(configs)
    prof = args.profile_dir + '/%s' % args.profile
    prof = profile.Profile(prof)
    if args.environment:
        env = configs.environments.pop(args.environment)
        ldap_conn = LDAP.LDAP(env,
                              user=ldap_user,
                              password=ldap_password,
                              basedn=configs.basedn)
    else:
        ldap_conn = LDAP.LDAP.from_config(configs).next()
    if args.users:
        users = args.users
    else:
        users = [i for i in ldap_conn.get_all_uids()]
    audits = defaultdict(list)
    for user in users:
        usearch = ldap_conn.user_search(user)
        the_audit = (prof
                     .audit(usearch,
                            explicit=True,
                            ignore_inherited=args.ignore))
        if the_audit['value'] != 3:
            continue
        key = the_audit.pop('name')
        audits[key].append(the_audit)
    if args.html:
        print profile.audits2html(audits)
    else:
        print yaml.dump(audits, default_flow_style=False)

def audit(args):
    ''' Perform an LDAP audit. Find all users, evaluate how well they match to
        profiles, and generate a report.
    '''
    configs = config.Config(args.config)
    ldap_user, ldap_password = ldap_creds(configs)
    profiles = [i for i in profile.Profile.from_directory(args.profile_dir)]
    if args.environment:
        env = configs.environments.pop(args.environment)
        ldap_conn = LDAP.LDAP(env,
                              user=ldap_user,
                              password=ldap_password,
                              basedn=configs.basedn)
    else:
        ldap_conn = LDAP.LDAP.from_config(configs).next()
    if args.users:
        users = args.users
    else:
        users = [i for i in ldap_conn.get_all_uids()]
    audits = defaultdict(list)
    for user in users:
        usearch = ldap_conn.user_search(user)
        usearch.found = True # set this explicitly since we obtained the list
                              # of users from LDAP
        the_audit = (profile
                     .Profile
                     .bulk_audit(usearch,
                                 profiles=profiles,
                                 ignore_inherited=args.ignore,
                                 explicit=args.explicit))
        key = the_audit.pop('name')
        audits[key].append(the_audit)
    if args.html:
        print profile.audits2html(audits)
    else:
        print yaml.dump(audits, default_flow_style=False)

def profile_suf(prof_name):
    ''' Ensure correct yaml extension for profiles found in profiles directory
    '''
    if prof_name.endswith('.yaml'):
        return prof_name
    tokens = prof_name.split('.')
    if len(tokens) == 1:
        return prof_name+'.yaml'
    return '.'.join(tokens[:-1])+'.yaml'

def profile_dumper(args):
    ''' Dump profiles to stdout.
    '''
    if args.single:
        profiles = ([profile.Profile(os.path.join(args.profile_dir,
                                                  args.single))])
    else:
        profiles = [i for i in profile.Profile.from_directory(args.profile_dir)]
    for prof in profiles:
        print 'Profile "%s"' % prof.name
        print prof

def propagate_pubkeys(args):
    ''' Copy a user's public key from chosen LDAP environment to other
        environments.
    '''
    configs = config.Config(args.config)
    ldap_user, ldap_password = ldap_creds(configs)
    origin = configs.environments.pop(args.environment)
    ldap_conn = LDAP.LDAP(origin,
                          user=ldap_user,
                          password=ldap_password,
                          basedn=configs.basedn)
    user = ldap_conn.search(basedn=configs.basedn,
                            filterstr='(uid=%s)' % args.user).next()
    for _, host in configs.environments.items():
        next_ldap = LDAP.LDAP(host,
                              user=ldap_user,
                              password=ldap_password,
                              basedn=configs.basedn)
        nextuser = next_ldap.search(basedn=configs.basedn,
                                    filterstr='(uid=%s)' % args.user).next()
        next_ldap.replace_attribute('sshPublicKey', nextuser, user.sshPublicKey)
        print 'Copied public key for user %s to LDAP host %s' % (args.user,
                                                                 next_ldap.host)
