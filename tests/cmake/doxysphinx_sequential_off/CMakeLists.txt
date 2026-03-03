# boilerplate to get CMake running
cmake_minimum_required(VERSION 3.22.0)
project(test-doxysphinx-sequential-off)

# SPL_DOXYSPHINX_SEQUENTIAL is expected to be passed via -DSPL_DOXYSPHINX_SEQUENTIAL=OFF

# ## IUT ####################################
include(${CMAKE_CURRENT_LIST_DIR}/../../../src/spl_core/common.cmake)

# ## test: SPL_DOXYSPHINX_EXTRA_ARGS with SPL_DOXYSPHINX_SEQUENTIAL=OFF #########
# given: SPL_DOXYSPHINX_SEQUENTIAL is explicitly OFF

# then: SPL_DOXYSPHINX_EXTRA_ARGS should be empty
if(NOT "${SPL_DOXYSPHINX_EXTRA_ARGS}" STREQUAL "")
    message(FATAL_ERROR "Failing Test: SPL_DOXYSPHINX_EXTRA_ARGS should be empty when SPL_DOXYSPHINX_SEQUENTIAL is OFF, but got: '${SPL_DOXYSPHINX_EXTRA_ARGS}'.")
endif()
