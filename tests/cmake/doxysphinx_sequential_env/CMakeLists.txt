# boilerplate to get CMake running
cmake_minimum_required(VERSION 3.22.0)
project(test-doxysphinx-sequential-env)

# SPL_DOXYSPHINX_SEQUENTIAL is expected to be set via environment variable

# ## IUT ####################################
include(${CMAKE_CURRENT_LIST_DIR}/../../../src/spl_core/common.cmake)

# ## test: SPL_DOXYSPHINX_EXTRA_ARGS via environment variable #########
# given: SPL_DOXYSPHINX_SEQUENTIAL env var is set to ON (by the Python test runner)

# then: SPL_DOXYSPHINX_EXTRA_ARGS should be --sequential
if(NOT "${SPL_DOXYSPHINX_EXTRA_ARGS}" STREQUAL "--sequential")
    message(FATAL_ERROR "Failing Test: SPL_DOXYSPHINX_EXTRA_ARGS should be '--sequential' when env var SPL_DOXYSPHINX_SEQUENTIAL is ON, but got: '${SPL_DOXYSPHINX_EXTRA_ARGS}'.")
endif()
