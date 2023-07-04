# given
cmake_minimum_required(VERSION 3.22.0)
project(test-common-cmake C ASM)

set(VARIANT mytestvariant)

# when
include(${CMAKE_CURRENT_LIST_DIR}/../../cmake/common.cmake)

# expect
set(string_with_underscore "abc/def/ghi")
_spl_slash_to_underscore(string_with_underscore ${string_with_underscore})
if (NOT string_with_underscore STREQUAL "abc_def_ghi")
    message(FATAL_ERROR "Failing Test case: string_with_underscore = ${string_with_underscore}.")
endif()

_spl_get_absolute_path(absolute_path "${PROJECT_SOURCE_DIR}/some_dir")
set(expected_path tests/common.cmake/some_dir)
string(FIND "${absolute_path}" "${expected_path}" out)
if (NOT "${out}" GREATER 0)
message(FATAL_ERROR "Failing Test case: ${absolute_path} does not contain ${expected_path}.")
endif()

_spl_get_absolute_path(absolute_path "${PROJECT_BINARY_DIR}/some_output")
set(expected_path out/test_cmake/common.cmake/some_output)
string(FIND "${absolute_path}" "${expected_path}" out)
if (NOT "${out}" GREATER 0)
    message(FATAL_ERROR "Failing Test case: ${absolute_path} does not contain ${expected_path}.")
endif()
