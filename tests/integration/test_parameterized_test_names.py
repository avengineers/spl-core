import textwrap
import xml.etree.ElementTree as ET

import pytest
from utils import SplProjectIntegrationTestBase


@pytest.mark.integration
class TestParameterizedTestNames(SplProjectIntegrationTestBase):
    def test_value_parameterized_test_is_named_by_index(self):
        """A value-parameterized test result keeps the name gtest gives it: the parameter index, not a print of the value."""
        variant = "Variant1"

        "A struct parameter without a printer: gtest would print its raw bytes, including a pointer"
        self.spl_project.artifacts.src_dir.joinpath("component", "test", "test_component.cc").write_text(
            textwrap.dedent(
                """
                #include <gtest/gtest.h>
                using namespace testing;

                extern "C"
                {
                #include "component.h"
                }

                #include "mockup_src_component.h"

                struct TestParam
                {
                    const char *description;
                    int value;
                };

                class component : public TestWithParam<TestParam>
                {
                };

                TEST_P(component, test_parameterized)
                {
                    CREATE_MOCK(mymock);
                    EXPECT_CALL(mymock, someInterfaceOfComponentB()).Times(1).WillOnce(Return(7));
                    EXPECT_EQ(7, someInterfaceOfComponent());
                }

                INSTANTIATE_TEST_SUITE_P(
                    componentSuite,
                    component,
                    Values(
                        TestParam{"first", 0},
                        TestParam{"second", 1}));
                """
            )
        )

        "Call IUT"
        result = self.spl_project.build(variant, "unittests")
        assert result.returncode == 0, "Execution shall not fail."

        "Expected test results are named by the parameter index"
        junitxml = self.spl_project.artifacts.get_build_dir(variant, "test").joinpath("src/component/junit.xml")
        assert junitxml.exists()
        testsuite = ET.parse(junitxml).getroot()  # noqa: S314
        names = sorted(test_case.attrib["name"] for test_case in testsuite.iter("testcase"))
        assert names == [
            "componentSuite/component.test_parameterized/0",
            "componentSuite/component.test_parameterized/1",
        ]
