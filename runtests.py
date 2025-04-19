import os
import sys
import argparse

import django
from django.conf import settings
from django.test.utils import get_runner


def run_tests(test_labels=None, verbosity=1, interactive=False, failfast=False):
    """
    Execute Django tests with configurable options.

    Args:
        test_labels (list): List of test modules or specific tests to run (e.g., ['xblog.tests.test_metaWeblog.MetaWeblogTestCase']).
        verbosity (int): Verbosity level (0=minimal, 1=normal, 2=verbose).
        interactive (bool): Allow interactive prompts (e.g., for debugging).
        failfast (bool): Stop on first failure.
    """
    # Default to xblog.tests if no labels provided
    test_labels = test_labels or ["xblog.tests"]

    # Set Django settings module
    os.environ["DJANGO_SETTINGS_MODULE"] = "xblog.tests.conf.settings"

    try:
        django.setup()
    except Exception as e:
        print(f"Failed to initialize Django: {e}")
        sys.exit(1)

    # Configure and run the test runner
    test_runner_class = get_runner(settings)
    test_runner = test_runner_class(
        verbosity=verbosity, interactive=interactive, failfast=failfast
    )
    failures = test_runner.run_tests(test_labels)

    sys.exit(failures)


def main():
    """
    Parse command-line arguments and run tests.
    """
    parser = argparse.ArgumentParser(description="Run Django tests for xblog.")
    parser.add_argument(
        "--verbosity", type=int, default=1, choices=[0, 1, 2], help="Verbosity level"
    )
    parser.add_argument(
        "--noinput", action="store_false", dest="interactive", help="Disable interactive prompts"
    )
    parser.add_argument(
        "--failfast", action="store_true", help="Stop on first failure"
    )
    parser.add_argument(
        "test_labels", nargs="*", default=["xblog.tests"], help="Test modules or specific tests to run (e.g., xblog.tests.test_metaWeblog.MetaWeblogTestCase)"
    )

    args = parser.parse_args()
    run_tests(
        test_labels=args.test_labels,
        verbosity=args.verbosity,
        interactive=args.interactive,
        failfast=args.failfast,
    )


if __name__ == "__main__":
    main()