include(../spl_test.cmake)

# mocks
spl_test_create_mock(add_executable)
spl_test_create_mock(target_compile_options)
spl_test_create_mock(set_target_properties)

# given
cmake_minimum_required(VERSION 3.22.0)
project(test C ASM)

set(VARIANT mytestvariant)
set(BUILD_KIT prod)
set(LINKER_OUTPUT_FILE main.exe)
set(LINKER_BYPRODUCTS_EXTENSIONS "hex")
set(LINKER_BYPRODUCT_HEX bibi.hex tina.map amadeus.mdf)

# when
include(${CMAKE_CURRENT_LIST_DIR}/../../../cmake/spl.cmake)

# expect
if(NOT LINK_TARGET_NAME STREQUAL "link")
    message(FATAL_ERROR "Failing Test case: LINK_TARGET_NAME = ${LINK_TARGET_NAME}.")
endif()

if(NOT LINK_FILE_BASENAME STREQUAL "main")
    message(FATAL_ERROR "Failing Test case: LINK_FILE_BASENAME = ${LINK_FILE_BASENAME}.")
endif()

if(NOT LINKER_BYPRODUCTS STREQUAL "main.hex;bibi.hex;tina.map;amadeus.mdf")
    message(FATAL_ERROR "Failing Test case: LINKER_BYPRODUCTS = ${LINKER_BYPRODUCTS}.")
endif()

spl_test_expect_is_called(add_executable 1)
spl_test_expect_is_called(target_compile_options 1)
spl_test_expect_is_called(set_target_properties 1)
