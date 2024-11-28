# boilerplate to get CMake running
cmake_minimum_required(VERSION 3.22.0)
project(test-common-cmake C ASM)
set(VARIANT mytestvariant)
set(BUILD_KIT prod)

# ## IUT ####################################
include(${CMAKE_CURRENT_LIST_DIR}/../../../cmake/common.cmake)

# ## test: _spl_slash_to_underscore #########
# given
set(string_with_slashes "abc/def/ghi")

# when
_spl_slash_to_underscore(string_with_underscore ${string_with_slashes})

# then
if(NOT string_with_underscore STREQUAL "abc_def_ghi")
    message(FATAL_ERROR "Failing Test case: string_with_slashes = ${string_with_slashes}.")
endif()

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
foreach(expected_component IN ITEMS some_external_component another_external_component)
    if(NOT "${expected_component}" IN_LIST COMPONENT_NAMES)
        message(FATAL_ERROR "Failing Test case: ${expected_component} not found inside ${COMPONENT_NAMES}.")
    endif()
endforeach()

# ## test: _spl_create_build_info_file (tests are written in test_cmake.py)#####
_spl_create_build_info_file()

# cleanup
unset(SOURCES)
unset(COMPONENT_NAMES)
