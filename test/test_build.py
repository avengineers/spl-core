#!/usr/bin/env python3

import unittest
import os.path
from utils import run_process


class TestBuild(unittest.TestCase):

    def test_build_spl__alpha(self):
        variant = 'spl/alpha'
        self.build_and_expect_default(variant)
        
    def test_build_spl__beta(self):
        variant = 'spl/beta'
        self.build_and_expect_default(variant)

    def test_build_spl__gamma(self):
        variant = 'spl/gamma'
        self.build_and_expect_default(variant)

    def build_and_expect_default(self, variant, target='default'):
        """build wrapper shall build the default target and related outputs."""

        exit_code = run_process([
            'build.bat',
            '--build',
            '--variants', variant,
            '--target', target,
            '--reconfigure'
        ])

        self.assertEqual(0, exit_code)
        self.expect_binary(variant)

    def expect_binary(self, variant, binType='exe'):
        """binary file of given variant shall exist."""
        self.assert_expected_file_exists(
            'build/{variant}/prod/{variant_underscore}.{bin}'.format(variant=variant, variant_underscore=variant.replace('/', '_'), bin=binType))

    def assert_expected_file_exists(self, expected_file):
        self.assertTrue(os.path.isfile(expected_file), 'File {expected_file} shall exist.'.format(expected_file=expected_file))
