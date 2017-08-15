#!/usr/bin/env python
"""attdict module
Convenience class for mocking objects from dictionaries.

Example:
    import jldap.attdict
    some_dict = jldap.attdict.Attdict({1:1})
"""
class Attdict(dict):
    ''' Convenience class for mocking objects from dictionaries.
    '''
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
