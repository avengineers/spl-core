"""
JUnit XML Merger

Merges multiple JUnit XML files into a single variant-level JUnit XML file.
This enables CI/CD tooling to consume aggregated test results from all components.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from junitparser import JUnitXml


class JUnitMergerError(Exception):
    """Exception raised when JUnit XML merging fails."""

    pass


class JUnitMerger:
    """
    Merges multiple JUnit XML files into a single variant-level JUnit XML file.

    This class provides functionality to aggregate test results from multiple
    components into a unified JUnit XML file for CI/CD tooling.
    """

    def __init__(self, input_files: List[str], output_file: str, variant: Optional[str] = None):
        """
        Initialize the JUnit merger.

        Args:
            input_files: List of paths to input JUnit XML files
            output_file: Path to output merged JUnit XML file
            variant: Optional variant name to prefix test suite names (e.g., "my_variant")

        Raises:
            ValueError: If input_files list is empty
        """
        if not input_files:
            raise ValueError("No input files provided for merging")

        self.input_files = input_files
        self.output_file = output_file
        self.variant = variant

    def merge(self) -> None:
        """
        Merge all input JUnit XML files into the output file.

        Raises:
            FileNotFoundError: If any input file doesn't exist
            Exception: If any input file contains malformed XML or validation fails
        """
        # Create merged JUnit XML container
        merged_xml = JUnitXml()

        # Process each input file
        for input_path in self.input_files:
            input_file = Path(input_path)

            if not input_file.exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")

            try:
                # Parse the input JUnit XML file
                xml = JUnitXml.fromfile(str(input_file))

                # Add all test suites from this file to the merged result
                for suite in xml:
                    # Make testsuite name unique by using parent directory if name is empty or generic
                    if not suite.name or suite.name == "(empty)":
                        parent_name = input_file.parent.name
                        if not parent_name:
                            raise JUnitMergerError(f"Cannot determine unique testsuite name for '{input_path}': testsuite name is empty and parent directory is root")
                        suite.name = parent_name

                    # Prefix suite name with variant if provided
                    if self.variant:
                        suite.name = f"{self.variant}.{suite.name}"

                    # Remove verbose output blocks from all testcases
                    for testcase in suite:
                        # Prefix classname with variant if provided
                        if self.variant and testcase.classname:
                            testcase.classname = f"{self.variant}.{testcase.classname}"

                        # Remove system-out and properties, but preserve system-err and result elements
                        testcase.system_out = None
                        # Clear properties by setting to empty list
                        if hasattr(testcase, "_elem") and testcase._elem is not None:
                            properties_elem = testcase._elem.find("properties")
                            if properties_elem is not None:
                                testcase._elem.remove(properties_elem)

                    merged_xml.add_testsuite(suite)

            except Exception as e:
                raise JUnitMergerError(f"Failed to parse JUnit XML file '{input_path}': {e}") from e

        # Write merged result to output file
        output_path = Path(self.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged_xml.write(str(output_path))

        # Validate the output
        self._validate_output()

    def _validate_output(self) -> None:
        """
        Validate that the merged output file is valid JUnit XML.

        Raises:
            Exception: If the output file cannot be parsed as valid JUnit XML
        """
        try:
            JUnitXml.fromfile(str(self.output_file))
        except Exception as e:
            raise JUnitMergerError(f"Validation failed: merged output is not valid JUnit XML: {e}") from e


def main() -> int:
    """
    Main entry point for command-line interface.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Merge multiple JUnit XML files into a single variant-level file")
    parser.add_argument("--output", required=True, help="Path to output merged JUnit XML file")
    parser.add_argument("--inputs", nargs="+", required=True, help="Paths to input JUnit XML files to merge")
    parser.add_argument("--variant", help="Optional variant name to prefix test suite names")

    args = parser.parse_args()

    try:
        merger = JUnitMerger(args.inputs, args.output, variant=args.variant)
        merger.merge()
        print(f"Successfully merged {len(args.inputs)} JUnit XML file(s) into {args.output}")
        return 0

    except Exception as e:
        print(f"ERROR: Failed to merge JUnit XML files: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
