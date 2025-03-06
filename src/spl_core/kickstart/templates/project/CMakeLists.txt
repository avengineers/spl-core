# cmake project definition
cmake_minimum_required(VERSION 3.24.0)
cmake_policy(VERSION 3.24)

# configure the current variant to be build
set(BUILD_KIT prod CACHE STRING "Target Group to build.")

include(${CMAKE_SOURCE_DIR}/variants/${VARIANT}/config.cmake)

if(BUILD_KIT STREQUAL prod)
    project(${VARIANT} C ASM)
else()
    # In case of test the project is a C++ project due to GTest usage
    project(${VARIANT} C ASM CXX)
endif()

# Fetch all external dependencies into modules directory
set(FETCHCONTENT_BASE_DIR ${CMAKE_SOURCE_DIR}/build/modules CACHE INTERNAL "")
set(FETCHCONTENT_QUIET FALSE)
include(FetchContent)

# Include spl-core
if(DEFINED ENV{SPLCORE_PATH})
    message(WARNING "SPLCORE_PATH defined! Use fixed SPL-CORE version from: $ENV{SPLCORE_PATH}")
    include($ENV{SPLCORE_PATH}/spl.cmake)
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

# add all components' include directories to the include paths of each component
foreach(component_name ${COMPONENT_NAMES})
    if(TARGET ${component_name})
        target_include_directories(${component_name} PUBLIC ${target_include_directories__INCLUDES})
    endif()
endforeach()
