#!/usr/bin/env python
"""
Persists the coverage report in htmlcov/ directory.

This script is a workaround to explicitly save the coverage report
and generate an html report.
`coverage run` isn't computing a coverage report let alone generating the report.
Correct mounts, permissions and pre-reqs are set up and the issue may be something else
as suggested here:
https://stackoverflow.com/a/53346768
Manually importing, cleaning up and invoking the coverage + explicitly saving
works as expected.
"""

from coverage import Coverage
import pytest

def build_coverage_report():
    """Run tests and generate an html coverage report.

    Equivalent to `coverage run` && `coverage html`,
    using the default configuration files:
    `.coveragerc` and `pytest.ini`.
    """
    cov = Coverage()
    cov.erase()
    cov.start()
    pytest.main()
    cov.stop()
    cov.save()
    cov.report()
    cov.html_report(directory='htmlcov')

if __name__ == '__main__':
    build_coverage_report()

