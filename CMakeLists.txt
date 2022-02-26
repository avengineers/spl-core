# cmake project definition
cmake_minimum_required(VERSION 3.22.0)

set(VARIANT ${FLAVOR}/${SUBSYSTEM} CACHE STRING "Variant to build.")
set(BUILD_KIT production CACHE STRING "Target Group to build.")

include(variants/${VARIANT}/config.cmake)
project(${VARIANT} C ASM)

#first time checkout submodules, ignore if existing
execute_process(
    COMMAND git submodule update --init --recursive
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    ERROR_QUIET
)

#consecutive times just pull changes
execute_process(
    COMMAND git submodule update --recursive
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
)

set(EXE_TARGET_NAME exe)

include(tools/cmake/common-macros.cmake)

# get variant specific feature configuration for build or test
include_directories("build/${VARIANT}/gen")

if(BUILD_KIT STREQUAL production)
    include(tools/cmake/build-kit-production.cmake)
endif()

if(BUILD_KIT STREQUAL test)
    include(tools/cmake/build-kit-test.cmake)
endif()

include(variants/${VARIANT}/parts.cmake)

configure_file(${CMAKE_SOURCE_DIR}/variants/config.h.in gen/config.h @ONLY)
