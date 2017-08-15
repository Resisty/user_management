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
import yaml
import argparse
import re

from bs4 import BeautifulSoup

IGNORE_FIELDS = ['owner',
                 'primary-gid-number',
                 'samba-group-mapping',
                 'samba-group-sid']
PATTERN = r'\.yaml'

class ProfileDumper(object):
    def __init__(self, pattern=PATTERN):
        self._profile_pattern = pattern
        self._html = BeautifulSoup('','html5lib')
        table = self._html.new_tag('table')
        table.attrs = {'style': 'border: 1px solid; border-width: 1px; border-color: #000000;'}
        self._html.append(table)
        thead = self._html.new_tag('thead')
        table.append(thead)
        tr = self._html.new_tag('tr')
        thead.append(tr)
        thead.attrs = {'style': 'background-color: #dbdbdb;'}

        for i in ['Name', 'Owner', 'Permissions']:
            th = self._html.new_tag('th')
            th.string = i
            tr.append(th)
        self._tbody = self._html.new_tag('tbody')
        table.append(self._tbody)

    @property
    def pattern(self):
        return self._profile_pattern
    @pattern.setter
    def pattern(self, p):
        self._profile_pattern = p

    def add(self, name, yml):
        owner = yml['owner']
        for i in IGNORE_FIELDS:
            try:
                yml.pop(i)
            except KeyError:
                continue
        tr = self._html.new_tag('tr')
        self._tbody.append(tr)
        yaml_string = yaml.dump(yml, default_flow_style=False)
        td = self._html.new_tag('td')
        tr.append(td)
        td.string = re.sub(self.pattern + '$', '', name)
        td = self._html.new_tag('td')
        tr.append(td)
        td.string = owner
        td = self._html.new_tag('td')
        tr.append(td)
        pre = self._html.new_tag('pre')
        td.append(pre)
        for line in yaml_string.split('\n'):
            p = self._html.new_tag('p')
            p.string = line
            pre.append(p)

    def add_dir(self, directory):
        for _,_,files in os.walk(directory):
            for f in files:
                if re.search(self.pattern, f):
                    with open(os.path.join(directory, f), 'r') as yml:
                        profile = yaml.load(yml)
                    self.add(f, profile)

    def dump(self):
        return str(self._html)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('profile_directory',
                        help='Profile yaml file storage directory. Does not \
                        search recursively.')
    parser.add_argument('-p', '--profile_pattern',
                        default=PATTERN,
                        help='Regular expression to match profile file names \
                        against')
    args = parser.parse_args()
    profiles = {}
    dumper = ProfileDumper(pattern=args.profile_pattern)
    dumper.add_dir(args.profile_directory)
    print dumper.dump()

if __name__ == '__main__':
    main()
