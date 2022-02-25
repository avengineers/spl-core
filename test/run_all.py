#!/usr/bin/env python3

"""
Main test function to execute all tests found in the current directory
"""

import re
import os
import sys
import logging
import argparse
import xmlrunner
import tempfile
import unittest
from pathlib import Path
from utils import get_output_folder

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%I:%M:%S', level=logging.DEBUG)


def load_test_cases(test_files=None, input_folder='.', name_pattern='test_*.py'):
    """
    :param test_files: List with full paths to the test scripts containing tests to be executed
    :param input_folder: Folder where to search for test scripts
    :param name_pattern: Test script filename pattern
    :return: unittest suite containing all tests to be executed
    """

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    # Specific test files
    if test_files:
        for module_path in test_files:
            module_location, module_name = os.path.split(module_path)
            testcase = loader.discover(
                start_dir=module_location, pattern=module_name)
            suite.addTest(testcase)
    # All test files in a folder
    else:
        suite.addTest(loader.discover(
            start_dir=input_folder, pattern=name_pattern))

    return suite


def execute_test_cases(suite, test_report):
    tmp_report = tempfile.TemporaryFile(mode='w+', encoding='iso-8859-1')
    test_result = xmlrunner.XMLTestRunner(
        tmp_report, descriptions=True, verbosity=3).run(suite)

    # Fix the report to be a valid xml format
    with open(test_report, 'w', encoding='iso-8859-1') as fp:
        fp.write("<?xml version=\"1.0\" ?>\n")
        fp.write("<test_suites>\n")

        tmp_report.seek(0)
        for line in tmp_report:
            line = re.sub(r"<\?xml version\=\"1\.0\" \?>", r"", line)
            fp.write(line)

        fp.write("</test_suites>\n")

    tmp_report.close()  # this also removes the temporary file

    return test_result.wasSuccessful()


def main():
    # Parse the input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--xmlfile', help="XML report file", nargs='?')
    parser.add_argument(
        '-t', '--testfiles', help="Full path to specific test files to be executed", nargs='+')
    args = parser.parse_args()

    os.chdir('test')

    if not args.xmlfile:
        out_folder = Path(get_output_folder())
        if not out_folder.is_dir():
            os.makedirs(out_folder.as_posix())
        test_report = os.path.join(get_output_folder(), 'test-report.xml')
    else:
        test_report = args.xmlfile

    # Load all test cases
    my_suite = load_test_cases(args.testfiles)

    # Execute all tests
    os.chdir('..')
    execute_test_cases(my_suite, test_report)

    return 0


if __name__ == '__main__':
    # Ugly hack to add the python modules to the python path be able to import them
    src_path = Path(Path(__file__).parent.as_posix(), '../src')
    sys.path.append(src_path.as_posix())
    sys.exit(main())
