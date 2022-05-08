# cmake project definition
cmake_minimum_required(VERSION 3.22.0)

#set variant from outside
set(VARIANT ${FLAVOR}/${SUBSYSTEM} CACHE STRING "Variant to build.")
set(BUILD_KIT production CACHE STRING "Target Group to build.")
set(EXE_TARGET_NAME exe)

#load variant specific configuration and toolchain
include(variants/${VARIANT}/config.cmake)

project(${VARIANT} C ASM)

#load common includes
include(tools/cmake/common-macros.cmake)
include(tools/cmake/common-functions.cmake)

if(BUILD_KIT STREQUAL production)
    include(tools/cmake/build-kit-production.cmake)
elseif(BUILD_KIT STREQUAL test)
    include(tools/cmake/build-kit-test.cmake)
endif()

# get variant specific feature configuration for build or test
include_directories("build/${VARIANT}/gen")
configure_file(${CMAKE_SOURCE_DIR}/variants/config.h.in gen/config.h @ONLY)
include(variants/${VARIANT}/parts.cmake)

checkout_git_submodules()
