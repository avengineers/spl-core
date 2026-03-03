# boilerplate to get CMake running
cmake_minimum_required(VERSION 3.22.0)
project(test-doxysphinx-sequential)

# SPL_DOXYSPHINX_SEQUENTIAL is expected to be passed via -DSPL_DOXYSPHINX_SEQUENTIAL=ON

# ## IUT ####################################
include(${CMAKE_CURRENT_LIST_DIR}/../../../src/spl_core/common.cmake)

# ## test: SPL_DOXYSPHINX_EXTRA_ARGS with SPL_DOXYSPHINX_SEQUENTIAL=ON #########
# given: SPL_DOXYSPHINX_SEQUENTIAL is ON (passed via cmake -D)

# then: SPL_DOXYSPHINX_EXTRA_ARGS should be --sequential
if(NOT "${SPL_DOXYSPHINX_EXTRA_ARGS}" STREQUAL "--sequential")
    message(FATAL_ERROR "Failing Test: SPL_DOXYSPHINX_EXTRA_ARGS should be '--sequential' when SPL_DOXYSPHINX_SEQUENTIAL is ON, but got: '${SPL_DOXYSPHINX_EXTRA_ARGS}'.")
endif()
