#!/usr/bin/env python
"""

Run and setup django xblog testing

"""

import os
import sys

import django
from django.conf import settings
import django.core.management as mgmt

def main():
    """
    execute the tests
    """
    os.environ['DJANGO_SETTINGS_MODULE'] = 'xblog.tests.conf.settings'
    django.setup()

    mgmt.call_command('shell')
if __name__ == '__main__':
    main()
