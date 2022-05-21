# cmake project definition
cmake_minimum_required(VERSION 3.22.0)

#set variant from outside
set(VARIANT ${FLAVOR}/${SUBSYSTEM} CACHE STRING "Variant to build.")
set(BUILD_KIT prod CACHE STRING "Target Group to build.")
set(EXE_TARGET_NAME exe)

#load common includes
include(tools/cmake/common-macros.cmake)

#load variant specific configuration and toolchain
include(variants/${VARIANT}/config.cmake)

project(${VARIANT} C ASM)

# build or test
if(BUILD_KIT STREQUAL prod)
    include(tools/cmake/build-kit-production.cmake)
elseif(BUILD_KIT STREQUAL test)
    include(tools/cmake/build-kit-test.cmake)
endif()

# get variant specific feature configuration for build or test
set(GEN_DIR ${CMAKE_SOURCE_DIR}/build/${VARIANT}/gen)
include_directories(${GEN_DIR})
configure_file(${CMAKE_SOURCE_DIR}/variants/config.h.in ${GEN_DIR}/config.h @ONLY)
include(variants/${VARIANT}/parts.cmake)

# get external git dependencies
checkout_git_submodules()
