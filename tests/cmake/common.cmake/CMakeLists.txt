# boilerplate to get CMake running
cmake_minimum_required(VERSION 3.22.0)
project(test-common-cmake C ASM CXX)
set(VARIANT mytestvariant)
set(BUILD_KIT prod)

# ## IUT ####################################
include(${CMAKE_CURRENT_LIST_DIR}/../../../src/spl_core/common.cmake)

# ## test: _spl_slash_to_underscore #########
# given
set(string_with_slashes "abc/def/ghi")

# when
_spl_slash_to_underscore(string_with_underscore ${string_with_slashes})

# then
if(NOT string_with_underscore STREQUAL "abc_def_ghi")
    message(FATAL_ERROR "Failing Test case: string_with_slashes = ${string_with_slashes}.")
endif()

# ## test: _spl_source_doc_name (source doc name collision avoidance) #########
# given two sources sharing a basename in different sub-directories of a component

# when
_spl_source_doc_name(doc_name_a "${CMAKE_CURRENT_LIST_DIR}/component/src/foo.c" "${CMAKE_CURRENT_LIST_DIR}/component")
_spl_source_doc_name(doc_name_b "${CMAKE_CURRENT_LIST_DIR}/component/test/foo.c" "${CMAKE_CURRENT_LIST_DIR}/component")

# then: doc names keep the relative path, so they stay distinct instead of both becoming "foo.c"
if(NOT doc_name_a STREQUAL "src/foo.c")
    message(FATAL_ERROR "Failing Test case: expected 'src/foo.c' but got '${doc_name_a}'.")
endif()

if(NOT doc_name_b STREQUAL "test/foo.c")
    message(FATAL_ERROR "Failing Test case: expected 'test/foo.c' but got '${doc_name_b}'.")
endif()

if(doc_name_a STREQUAL doc_name_b)
    message(FATAL_ERROR "Failing Test case: source doc names collide for same-basename files.")
endif()

# and: a source outside the component directory falls back to its basename
_spl_source_doc_name(doc_name_ext "${CMAKE_CURRENT_LIST_DIR}/other/bar.c" "${CMAKE_CURRENT_LIST_DIR}/component")
if(NOT doc_name_ext STREQUAL "bar.c")
    message(FATAL_ERROR "Failing Test case: expected 'bar.c' but got '${doc_name_ext}'.")
endif()

# ## test: _spl_filter_own_sources (source docs of NO_FOREIGN_SOURCE_DOCS components) #########
# given sources inside the component, outside of it, and in a sibling that shares its name as prefix
set(_own_src "${CMAKE_CURRENT_LIST_DIR}/component/src/a.c")
set(_own_test "${CMAKE_CURRENT_LIST_DIR}/component/test/b.cc")
set(_foreign "${CMAKE_CURRENT_LIST_DIR}/other/c.c")
set(_sibling "${CMAKE_CURRENT_LIST_DIR}/component_b/src/d.c")

# when
_spl_filter_own_sources(own_sources "${CMAKE_CURRENT_LIST_DIR}/component" "${_own_src};${_foreign};${_own_test};${_sibling}")

# then: only the sources inside the component directory remain, in their original order
if(NOT "${own_sources}" STREQUAL "${_own_src};${_own_test}")
    message(FATAL_ERROR "Failing Test case: expected '${_own_src};${_own_test}' but got '${own_sources}'.")
endif()

# and: a component without own sources gets an empty list
_spl_filter_own_sources(no_own_sources "${CMAKE_CURRENT_LIST_DIR}/component" "${_foreign};${_sibling}")
if(NOT "${no_own_sources}" STREQUAL "")
    message(FATAL_ERROR "Failing Test case: expected an empty list but got '${no_own_sources}'.")
endif()

# and: a source on another drive is not inside the component, although no relative path to it starts with '..'
if(WIN32)
    _spl_filter_own_sources(other_drive_sources "C:/project/component" "Z:/elsewhere/e.c")
    if(NOT "${other_drive_sources}" STREQUAL "")
        message(FATAL_ERROR "Failing Test case: expected an empty list but got '${other_drive_sources}'.")
    endif()
endif()

# ## test: _spl_clanguru_docs_options (Jinja raw tags are optional) #########
# given the default configuration

# when
_spl_clanguru_docs_options(clanguru_default_options)

# then: listings keep their Jinja raw tags, as before the option existed
if(NOT clanguru_default_options STREQUAL "--format;rst;--jinja-raw-tags")
    message(FATAL_ERROR "Failing Test case: expected '--format;rst;--jinja-raw-tags' but got '${clanguru_default_options}'.")
endif()

# given a project that renders no document through Jinja
set(SPL_SOURCE_DOCS_JINJA_RAW_TAGS OFF)

# when
_spl_clanguru_docs_options(clanguru_plain_options)

# then
if(NOT clanguru_plain_options STREQUAL "--format;rst")
    message(FATAL_ERROR "Failing Test case: expected '--format;rst' but got '${clanguru_plain_options}'.")
endif()

# cleanup
unset(SPL_SOURCE_DOCS_JINJA_RAW_TAGS)

# ## test: _spl_get_absolute_path #########
# when
_spl_get_absolute_path(absolute_path "${PROJECT_SOURCE_DIR}/some_dir")

# then
set(expected_path tests/cmake/common.cmake/some_dir)
string(FIND "${absolute_path}" "${expected_path}" out)

if(NOT "${out}" GREATER 0)
    message(FATAL_ERROR "Failing Test case: ${absolute_path} does not contain ${expected_path}.")
endif()

# when
_spl_get_absolute_path(absolute_path "${PROJECT_BINARY_DIR}/some_output")

# then
set(expected_path out/test_cmake/common.cmake/some_output)
string(FIND "${absolute_path}" "${expected_path}" out)

if(NOT "${out}" GREATER 0)
    message(FATAL_ERROR "Failing Test case: ${absolute_path} does not contain ${expected_path}.")
endif()

# ## test: spl_add_source #########
# given
set(source_file src/some_source_file.c)
set(other_source_file src/some_other_source_file.c)

# when
spl_add_source(${source_file})
spl_add_source(${other_source_file})

# then
_spl_get_absolute_path(expected_source_file "${source_file}")
_spl_get_absolute_path(expected_other_source_file "${other_source_file}")
_spl_get_absolute_path(unexpected_source_file "not_expected.c")

if(NOT expected_source_file IN_LIST SOURCES)
    message(FATAL_ERROR "Failing Test case: ${expected_source_file} not found inside ${SOURCES}.")
endif()

if(NOT expected_other_source_file IN_LIST SOURCES)
    message(FATAL_ERROR "Failing Test case: ${expected_other_source_file} not found inside ${SOURCES}.")
endif()

if(unexpected_source_file IN_LIST SOURCES)
    message(FATAL_ERROR "Failing Test case: ${unexpected_source_file} not found inside ${SOURCES}.")
endif()

# cleanup
unset(SOURCES)

# ## test: spl_add_test_source #########

# given
set(test_source_file test/some_test_source_file.c)
set(other_test_source_file test/some_other_test_source_file.c)

# when
spl_add_test_source(${test_source_file})
spl_add_test_source(${other_test_source_file})

# then
_spl_get_absolute_path(expected_test_source_file "${test_source_file}")
_spl_get_absolute_path(expected_other_test_source_file "${other_test_source_file}")
_spl_get_absolute_path(unexpected_test_source_file "not_expected.c")

if(NOT expected_test_source_file IN_LIST TEST_SOURCES)
    message(FATAL_ERROR "Failing Test case: ${expected_test_source_file} not found inside ${TEST_SOURCES}.")
endif()

if(NOT expected_other_test_source_file IN_LIST TEST_SOURCES)
    message(FATAL_ERROR "Failing Test case: ${expected_other_test_source_file} not found inside ${TEST_SOURCES}.")
endif()

if(unexpected_test_source_file IN_LIST TEST_SOURCES)
    message(FATAL_ERROR "Failing Test case: ${unexpected_test_source_file} not found inside ${TEST_SOURCES}.")
endif()

# cleanup
unset(TEST_SOURCES)

# ## test: spl_add_provided_interface #########
# given
set(provided_interface_dir src/provided/interface_dir)
set(other_provided_interface_dir src/other/provided_interface_dir)

# when
spl_add_provided_interface(${provided_interface_dir})
spl_add_provided_interface(${other_provided_interface_dir})

# then
_spl_get_absolute_path(expected_provided_interface_dir "${provided_interface_dir}")
_spl_get_absolute_path(expected_other_provided_interface_dir "${other_provided_interface_dir}")

if(NOT expected_provided_interface_dir IN_LIST PROVIDED_INTERFACES)
    message(FATAL_ERROR "Failing Test case: ${expected_provided_interface_dir} not found inside ${PROVIDED_INTERFACES}.")
endif()

if(NOT expected_other_provided_interface_dir IN_LIST PROVIDED_INTERFACES)
    message(FATAL_ERROR "Failing Test case: ${expected_other_provided_interface_dir} not found inside ${PROVIDED_INTERFACES}.")
endif()

# cleanup
unset(PROVIDED_INTERFACES)

# ## test: spl_add_required_interface #########
# given
set(required_component src/required_component)
set(other_required_component src/other_required_component)

# when
spl_add_required_interface(${required_component})
spl_add_required_interface(${other_required_component})

# then
_spl_slash_to_underscore(expected_required_component ${required_component})
_spl_slash_to_underscore(expected_other_required_component ${other_required_component})

if(NOT expected_required_component IN_LIST REQUIRED_INTERFACES)
    message(FATAL_ERROR "Failing Test case: ${expected_required_component} not found inside ${REQUIRED_INTERFACES}.")
endif()

if(NOT expected_other_required_component IN_LIST REQUIRED_INTERFACES)
    message(FATAL_ERROR "Failing Test case: ${expected_other_required_component} not found inside ${REQUIRED_INTERFACES}.")
endif()

# cleanup
unset(REQUIRED_INTERFACES)

# ## test: spl_add_component ###############

# given
set(some_file src/some_file.c)
set(some_other_file src/some_other_file.c)

# when
spl_add_component(component)
spl_add_component(some_other_component)
set_target_properties(component PROPERTIES LINKER_LANGUAGE C)

# then
if(NOT "component" IN_LIST COMPONENT_NAMES)
    message(FATAL_ERROR "Failing Test case: component not found inside ${COMPONENT_NAMES}.")
endif()

# cleanup
unset(SOURCES)
unset(COMPONENT_NAMES)

# ## test: spl_add_named_component ############

# given
# some external component with relative path
set(some_external_component external_package/some_external_component)

# another external component with absolute path
set(another_external_component ${CMAKE_CURRENT_LIST_DIR}/external_package/another_external_component)

# when
spl_add_named_component(some_external_component)
spl_add_named_component(another_external_component)

# then
# Note: component names are now derived from the path when a create component NAME is specified
foreach(expected_component IN ITEMS some_external_component another_external_component_name)
    if(NOT "${expected_component}" IN_LIST COMPONENT_NAMES)
        message(FATAL_ERROR "Failing Test case: ${expected_component} not found inside ${COMPONENT_NAMES}.")
    endif()
endforeach()

# ## test: _spl_create_build_info_file (tests are written in test_cmake.py)#####
_spl_create_build_info_file()

# cleanup
unset(SOURCES)
unset(COMPONENT_NAMES)

# ## test: _spl_set_test_compile_and_link_options #########
message(STATUS "CMAKE_C_COMPILER_ID: ${CMAKE_C_COMPILER_ID}")
message(STATUS "CMAKE_C_COMPILER_VERSION: ${CMAKE_C_COMPILER_VERSION}")
message(STATUS "CMAKE_CXX_COMPILER_ID: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "CMAKE_CXX_COMPILER_VERSION: ${CMAKE_CXX_COMPILER_VERSION}")

# Act
_spl_set_test_compile_and_link_options("GNU" "13.1.0")

# Assert
if(NOT "-ggdb" IN_LIST TEST_COMPILE_OPTIONS)
    message(FATAL_ERROR "Failing Test case: -ggdb not found inside ${TEST_COMPILE_OPTIONS}.")
endif()

if(NOT "-ggdb" IN_LIST COMPONENT_TEST_COMPILE_OPTIONS)
    message(FATAL_ERROR "Failing Test case: -ggdb not found inside ${COMPONENT_TEST_COMPILE_OPTIONS}.")
endif()

if("-fcondition-coverage" IN_LIST COMPONENT_TEST_COMPILE_OPTIONS)
    message(FATAL_ERROR "Failing Test case: -fcondition-coverage found inside ${COMPONENT_TEST_COMPILE_OPTIONS}.")
endif()

if(NOT "-ggdb" IN_LIST TEST_LINK_OPTIONS)
    message(FATAL_ERROR "Failing Test case: -ggdb not found inside ${TEST_LINK_OPTIONS}.")
endif()

if("-fcondition-coverage" IN_LIST TEST_LINK_OPTIONS)
    message(FATAL_ERROR "Failing Test case: -fcondition-coverage found inside ${TEST_LINK_OPTIONS}.")
endif()

# Act
_spl_set_test_compile_and_link_options("GNU" "14.1.0")

# Assert
if("-fcondition-coverage" IN_LIST COMPONENT_TEST_COMPILE_OPTIONS)
    message(FATAL_ERROR "Failing Test case: -fcondition-coverage found inside ${COMPONENT_TEST_COMPILE_OPTIONS}.")
endif()

if("-fcondition-coverage" IN_LIST TEST_LINK_OPTIONS)
    message(FATAL_ERROR "Failing Test case: -fcondition-coverage found inside ${TEST_LINK_OPTIONS}.")
endif()

# Act
_spl_set_test_compile_and_link_options("GNU" "14.2.0")

# Assert
if(NOT "-fcondition-coverage" IN_LIST COMPONENT_TEST_COMPILE_OPTIONS)
    message(FATAL_ERROR "Failing Test case: -fcondition-coverage not found inside ${COMPONENT_TEST_COMPILE_OPTIONS}.")
endif()

if(NOT "-fcondition-coverage" IN_LIST TEST_LINK_OPTIONS)
    message(FATAL_ERROR "Failing Test case: -fcondition-coverage not found inside ${TEST_LINK_OPTIONS}.")
endif()

# Act
_spl_set_test_compile_and_link_options("GNU" "14.2.1")

# Assert
if("-fcondition-coverage" IN_LIST TEST_COMPILE_OPTIONS)
    message(FATAL_ERROR "Failing Test case: -fcondition-coverage found inside ${TEST_COMPILE_OPTIONS}.")
endif()

if(NOT "-fcondition-coverage" IN_LIST COMPONENT_TEST_COMPILE_OPTIONS)
    message(FATAL_ERROR "Failing Test case: -fcondition-coverage not found inside ${COMPONENT_TEST_COMPILE_OPTIONS}.")
endif()

if(NOT "-fcondition-coverage" IN_LIST TEST_LINK_OPTIONS)
    message(FATAL_ERROR "Failing Test case: -fcondition-coverage not found inside ${TEST_LINK_OPTIONS}.")
endif()

# Act
# The next macro call fails. This is an explorative test to show that compiler id "BIBI" is not supported.
# Mocking of method "message()" sadly does not work.
# _spl_set_test_compile_and_link_options("BIBI" "1.2.3")
