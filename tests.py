#!/usr/bin/env python
"""config module
Run unit tests

Example:
    python tests.py

"""
import sys
import unittest
import importlib

PACKAGE = 'jldaptests'

if __name__ == '__main__':
    EXIT_CODE = 0
    PKG = importlib.import_module(PACKAGE)
    for modname in PKG.__all__:
        module = importlib.import_module('%s.%s' % (PACKAGE, modname))
        SUITE = module.suite()
        EXIT_CODE |= not unittest.TextTestRunner().run(SUITE).wasSuccessful()
    sys.exit(EXIT_CODE)
