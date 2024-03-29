# cmake project definition
cmake_minimum_required(VERSION 3.24.0)
cmake_policy(VERSION 3.24)

set(BUILD_KIT prod CACHE STRING "Target Group to build.")

include(${CMAKE_SOURCE_DIR}/variants/${VARIANT}/config.cmake)

if(BUILD_KIT STREQUAL prod)
    project(${VARIANT} C ASM)
else()
    project(${VARIANT} C ASM CXX)
    set(VARIANT_ADDITIONAL_COMPILE_C_FLAGS -Dstatic= -save-temps)
endif()

# Fetch all external dependencies into modules directory
set(FETCHCONTENT_BASE_DIR ${CMAKE_SOURCE_DIR}/build/modules CACHE INTERNAL "")
set(FETCHCONTENT_QUIET FALSE)
include(FetchContent)

# Include spl-core
if(DEFINED ENV{SPLCORE_PATH})
    message(WARNING "SPLCORE_PATH defined! Use fixed SPL-CORE version from: $ENV{SPLCORE_PATH}")
    include($ENV{SPLCORE_PATH}/cmake/spl.cmake)
else()
    # Fetch spl-core
    FetchContent_Declare(
        spl-core
        GIT_REPOSITORY https://github.com/avengineers/spl-core.git
        GIT_TAG develop
    )
    FetchContent_MakeAvailable(spl-core)

    # Include spl-core
    include(${spl-core_SOURCE_DIR}/cmake/spl.cmake)
endif()

include(${CMAKE_SOURCE_DIR}/variants/${VARIANT}/parts.cmake)

# TODO: refactor/remove; we want to explicitly add includes where required
foreach(component_name ${COMPONENT_NAMES})
    target_include_directories(${component_name} PUBLIC ${target_include_directories__INCLUDES})
endforeach()
