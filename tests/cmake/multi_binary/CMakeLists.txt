# boilerplate to get CMake running
cmake_minimum_required(VERSION 3.22.0)
project(test-multi-binary C ASM CXX)
set(VARIANT mytestvariant)
set(BUILD_KIT prod)

# ## IUT ####################################
include(${CMAKE_CURRENT_LIST_DIR}/../../../src/spl_core/common.cmake)

# ## test: spl_add_component with multi-binary support ###############

# given - one extra executable
set(LINK_TARGET_NAME "default_target_executable")
add_executable(${LINK_TARGET_NAME})
add_executable(app1)

# when - Add component to default and custom executable
spl_add_component(test_component)
spl_add_component(test_component app1)

# then
foreach(expected_component IN ITEMS app1_test_component test_component)
    if(NOT "${expected_component}" IN_LIST COMPONENT_NAMES)
        message(FATAL_ERROR "Failing Test case: ${expected_component} not found inside ${COMPONENT_NAMES}.")
    endif()
endforeach()

# some external component with relative path
set(some_external_component external/component)

# when
spl_add_named_component(some_external_component app1)

# then
if(NOT "app1_some_external_component" IN_LIST COMPONENT_NAMES)
    message(FATAL_ERROR "Failing Test case: app1_some_external_component not found inside ${COMPONENT_NAMES}.")
endif()
