# Define the SPL Core root directory to be used to refer to files
# relative to the SPL Core installation directory.
set(SPL_CORE_ROOT_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})
set(SPL_CORE_CMAKE_DIRECTORY ${SPL_CORE_ROOT_DIRECTORY})
set(SPL_CORE_PYTHON_DIRECTORY ${SPL_CORE_ROOT_DIRECTORY})

# Always create a compile_commands.json file for C/C++ intellisense / CMake Tools extension
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# The link target needs a name. This is not the name of the executable.
set(LINK_TARGET_NAME link)

# The variant's name is used to determine the base name of the created binaries.
string(REPLACE "/" "_" BINARY_BASENAME ${VARIANT})

# Set SPL relevant variables as environment variables.
# Can easily be extended in CMakeLists.txt of project.
# Also used for KConfig variable expansion.
list(APPEND ENVVARS FLAVOR SUBSYSTEM VARIANT BUILD_KIT BUILD_TYPE BINARY_BASENAME CMAKE_SOURCE_DIR)

foreach(ENVVAR IN LISTS ENVVARS)
    set(ENV{${ENVVAR}} "${${ENVVAR}}")
endforeach()

# Include common CMake functions and macros
include(${SPL_CORE_CMAKE_DIRECTORY}/common.cmake)

# Include and run KConfig
include(${SPL_CORE_CMAKE_DIRECTORY}/kconfig.cmake)

if(EXISTS ${AUTOCONF_CMAKE})
    include(${AUTOCONF_CMAKE})
endif(EXISTS ${AUTOCONF_CMAKE})

if(BUILD_KIT STREQUAL prod)
    # set default link target output name and extension
    if(LINKER_OUTPUT_FILE)
        get_filename_component(LINK_FILE_BASENAME ${LINKER_OUTPUT_FILE} NAME_WE)
        get_filename_component(LINK_FILE_EXTENSION ${LINKER_OUTPUT_FILE} EXT)

        # add variant specific linker script if defined
        if(VARIANT_LINKER_FILE)
            list(APPEND LINK_TARGET_DEPENDS ${VARIANT_LINKER_FILE})
        endif(VARIANT_LINKER_FILE)

        # create executable
        add_executable(${LINK_TARGET_NAME} ${LINK_TARGET_DEPENDS})
        target_compile_options(${LINK_TARGET_NAME} PRIVATE ${VARIANT_ADDITIONAL_LINK_FLAGS})
        set_target_properties(${LINK_TARGET_NAME} PROPERTIES
            OUTPUT_NAME ${LINK_FILE_BASENAME}
            SUFFIX ${LINK_FILE_EXTENSION}
            LINK_DEPENDS "${LINK_TARGET_DEPENDS}"
        )

        if(LINKER_BYPRODUCTS_EXTENSIONS)
            # combine basename and byproduct extension
            string(REPLACE "," ";" LINKER_BYPRODUCTS "${LINKER_BYPRODUCTS_EXTENSIONS}")
            list(TRANSFORM LINKER_BYPRODUCTS PREPEND ${LINK_FILE_BASENAME}.)
        endif(LINKER_BYPRODUCTS_EXTENSIONS)

        if(LINKER_BYPRODUCT_HEX)
            list(APPEND LINKER_BYPRODUCTS ${LINKER_BYPRODUCT_HEX})
        endif(LINKER_BYPRODUCT_HEX)

        if(LINKER_BYPRODUCT_MAP)
            list(APPEND LINKER_BYPRODUCTS ${LINKER_BYPRODUCT_MAP})
        endif(LINKER_BYPRODUCT_MAP)

        if(LINKER_BYPRODUCT_MDF)
            list(APPEND LINKER_BYPRODUCTS ${LINKER_BYPRODUCT_MDF})
        endif(LINKER_BYPRODUCT_MDF)

        if(LINKER_BYPRODUCT_OTHERS)
            string(REPLACE "," ";" LINKER_BYPRODUCTS_TMP "${LINKER_BYPRODUCT_OTHERS}")
            list(APPEND LINKER_BYPRODUCTS ${LINKER_BYPRODUCTS_TMP})
        endif(LINKER_BYPRODUCT_OTHERS)

        if(LINKER_BYPRODUCTS)
            add_custom_target(
                linker_byproducts ALL
                COMMAND ${CMAKE_COMMAND} -E true
                DEPENDS ${LINKER_OUTPUT_FILE}
                BYPRODUCTS ${LINKER_BYPRODUCTS}
            )
        endif(LINKER_BYPRODUCTS)
    endif(LINKER_OUTPUT_FILE)
elseif(BUILD_KIT STREQUAL test)
    _spl_get_google_test()
    include(CTest)
    list(APPEND CMAKE_CTEST_ARGUMENTS "--output-on-failure")

    add_custom_target(coverage)
else()
    message(FATAL_ERROR "Invalid BUILD_KIT selected!")
endif(BUILD_KIT STREQUAL prod)

# # Things to be done at the very end of configure phase as if they would be at bottom of CMakelists.txt
cmake_language(DEFER DIRECTORY ${CMAKE_SOURCE_DIR} CALL _spl_hook_end_of_configure())

function(_spl_hook_end_of_configure)
    if(BUILD_KIT STREQUAL test)
        _spl_coverage_create_overall_report()
        _spl_create_docs_target()
        _spl_create_reports_target()
    endif(BUILD_KIT STREQUAL test)
    _spl_create_build_info_file()
endfunction(_spl_hook_end_of_configure)

# # This is one possibility to open guiconfig of kconfiglib. VSCode task is the preferred solution
set(_CONFIGURATION_TARGET configuration.stamp)
add_custom_command(
    OUTPUT ${_CONFIGURATION_TARGET}
    COMMAND set "KCONFIG_CONFIG=${CMAKE_SOURCE_DIR}/variants/${VARIANT}/config.txt" && cd ${CMAKE_SOURCE_DIR} && guiconfig
)

add_custom_target(configuration DEPENDS ${_CONFIGURATION_TARGET})
