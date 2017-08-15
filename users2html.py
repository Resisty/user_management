#!/usr/bin/env python
# =======================================
#
#  File Name : profile2html.py
#
#  Purpose :
#
#  Creation Date : 12-08-2016
#
#  Last Modified : Tue Aug 16 08:54:25 2016
#
#  Created By : Brian Auron
#
# ========================================
import os
import sys
import yaml
import argparse
import re

from bs4 import BeautifulSoup
from jldap import LDAP, config

CONFIG = os.path.expanduser('~/.ldap.yml')

class UserDumper(object):
    def __init__(self):
        self._html = BeautifulSoup('','html5lib')
        table = self._html.new_tag('table')
        table.attrs = {'style': 'border: 1px solid; border-width: 1px; border-color: #000000;'}
        self._html.append(table)
        thead = self._html.new_tag('thead')
        table.append(thead)
        tr = self._html.new_tag('tr')
        thead.append(tr)
        thead.attrs = {'style': 'background-color: #dbdbdb;'}

        for i in ['Name', 'Permissions']:
            th = self._html.new_tag('th')
            th.string = i
            tr.append(th)
        self._tbody = self._html.new_tag('tbody')
        table.append(self._tbody)

    def add(self, user):
        ''' Should be an LDAP.LDAP.user_search() result
        '''
        tr = self._html.new_tag('tr')
        self._tbody.append(tr)
        td = self._html.new_tag('td')
        tr.append(td)
        td.string = user.name
        td = self._html.new_tag('td')
        tr.append(td)
        pre = self._html.new_tag('pre')
        td.append(pre)
        yaml_string = yaml.dump(user._permissions, default_flow_style=False)
        for line in yaml_string.split('\n'):
            p = self._html.new_tag('p')
            p.string = line
            pre.append(p)

    def dump(self):
        return str(self._html)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        default=CONFIG,
                        help='Regular expression to match profile file names \
                        against')
    args = parser.parse_args()
    conf = config.Config(args.config)
    phx = LDAP.LDAP.from_config(conf).next()
    dumper = UserDumper()
    all_users = phx.get_all_uids()
    for user in all_users:
        dumper.add(phx.user_search(user))
    print dumper.dump()

if __name__ == '__main__':
    main()
