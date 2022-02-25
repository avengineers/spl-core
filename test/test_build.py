#!/usr/bin/env python3

import unittest
import os.path
from utils import run_process


class TestBuild(unittest.TestCase):

    def test_build_spl__alpha(self):
        self.build_and_expect_default('spl/alpha')
        
    def test_build_spl__beta(self):
        self.build_and_expect_default('spl/beta')

    def test_build_spl__gamma(self):
        self.build_and_expect_default('spl/gamma')

    def build_and_expect_default(self, variant, target='default'):
        """build wrapper shall build the default target and related outputs."""

        exit_code = run_process([
            'spl.bat',
            '--build',
            '--variants', variant,
            '--target', target,
            '--reconfigure'
        ])

        self.assertEqual(0, exit_code)
        self.assert_expected_file_exists(
            'build/{variant}/configure-default.log'.format(variant=variant))
        self.assert_expected_file_exists(
            'build/{variant}/build-default.log'.format(variant=variant))
        self.expect_binary(variant)

    def expect_binary(self, variant, binType='exe'):
        """Hex file of given variant shall exist."""
        self.assert_expected_file_exists(
            'build/{variant}/{variant_underscore}.{bin}'.format(variant=variant, variant_underscore=variant.replace('/', '_'), bin=binType))

    def assert_expected_file_exists(self, expected_file):
        self.assertTrue(os.path.isfile(expected_file))
