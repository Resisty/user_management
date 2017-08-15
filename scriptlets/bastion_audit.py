#!/usr/bin/env python
import collections
import sys
import os
import re
import yaml

LDAPCONF = os.path.expanduser('~/.ldap.yml')

def members(conn, bdn, flt, atr):
    tmp = []
    results = conn.search(basedn=bdn,
                          filterstr=flt,
                          attrlist=atr)
    for i in results:
        try:
            for j in i.uniqueMember:
                if not re.search(r'ou=user(s|-disabled)', j): #,' not in j:
                    toks = j.split(',')
                    cn = toks[0]
                    newbdn = ','.join(toks[1:])
                    sub = {j: members(conn, newbdn, '(%s)' % cn, atr)}
                    tmp.append(sub)
                else:
                    tmp.append(j)
        except KeyError:
            pass
    return tmp
def main():
    conf = c.Config(LDAPCONF)
    conns = l.LDAP.from_config(conf)
    phx = None
    for i in conns:
        if i.host == 'ds-master.example.com':
            phx = i
            break
    if not phx:
        print('No connection to PHX. WTF')
        sys.exit(1)
    phx.basedn = 'ou=roles,ou=groups,dc=example,dc=com'
    kwargs = {'filterstr': '(cn=*)',
              'attrlist': ['uniqueMember']}
    results = [i for i in phx.search(**kwargs)]
    tree = collections.defaultdict(list)
    for item in results:
        toks = item.dn.split(',')
        cn = toks[0]
        newbdn = ','.join(toks[1:])
        tree[item.dn] = members(phx, newbdn, '(%s)' % cn, kwargs['attrlist'])
    print(yaml.dump(tree, default_flow_style=False))
if __name__ == '__main__':
    if __package__ is None:
        (sys
         .path
         .append(os
                 .path
                 .dirname(os
                          .path
                          .dirname(os
                                   .path
                                   .abspath(__file__)
                                  )
                         )
                )
        )
        from jldap import LDAP as l, config as c
    main()
