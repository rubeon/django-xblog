#!/usr/bin/env python
"""

Run and setup django xblog testing

"""

import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def main():
    """
    execute the tests
    """
    os.environ['DJANGO_SETTINGS_MODULE'] = 'xblog.tests.conf.settings'
    django.setup()
    test_runner_class = get_runner(settings)
    test_runner = test_runner_class()
    failures = test_runner.run_tests(["xblog.tests"])
    sys.exit(bool(failures))

if __name__ == '__main__':
    main()
