# given
cmake_minimum_required(VERSION 3.22.0)
project(test-common-cmake C ASM)

set(VARIANT mytestvariant)

# when
include(${CMAKE_CURRENT_LIST_DIR}/../../common.cmake)

# expect
if (NOT LINK_TARGET_NAME STREQUAL "link")
    message(FATAL_ERROR "Failing Test case: LINK_TARGET_NAME = ${LINK_TARGET_NAME}.")
endif()

set(string_with_underscore "abc/def/ghi")
_spl_slash_to_underscore(string_with_underscore ${string_with_underscore})
if (NOT string_with_underscore STREQUAL "abc_def_ghi")
    message(FATAL_ERROR "Failing Test case: string_with_underscore = ${string_with_underscore}.")
endif()

_spl_get_absolute_path(absolute_path "/test")
string(FIND "${absolute_path}" "cmake/test/common.cmake/test" out)
if (NOT "${out}" GREATER 0)
    message(FATAL_ERROR "Failing Test case: absolute_path = ${absolute_path}.")
endif()

# Components are refered by their relative path to the project
set(component_path "abc/def/ghi")
_spl_get_component_name_from_path(component_name ${component_path})
if (NOT component_name STREQUAL "abc_def_ghi")
    message(FATAL_ERROR "Failing Test case: component_name = ${component_name}.")
endif()

# External components are refered by the hash of their path
set(component_path "c:/abc/def/ghi")
_spl_get_component_name_from_path(component_name ${component_path})
if (NOT component_name STREQUAL "840cb7416f202751")
    message(FATAL_ERROR "Failing Test case: component_name = ${component_name}.")
endif()

# Component path is the component relative path to the project
set(project_dir "c:/abc")
set(component_dir "c:/abc/def/comp")
_spl_get_component_path(component_path ${project_dir} ${component_dir})
if (NOT component_path STREQUAL "def/comp")
    message(FATAL_ERROR "Failing Test case: component_path = ${component_path}.")
endif()

# External component path is the component absolute path
set(project_dir "c:/abc/def/ghi")
set(component_dir "c:/abc/comp")
_spl_get_component_path(component_path ${project_dir} ${component_dir})
if (NOT component_path STREQUAL "c:/abc/comp")
    message(FATAL_ERROR "Failing Test case: component_path = ${component_path}.")
endif()

# TODO: does not work on Github
# string(FIND "${absolute_path}" "C:" out)
# if (NOT "${out}" EQUAL 0)
#     message(FATAL_ERROR "Failing Test case: absolute_path = ${absolute_path}.")
# endif()
