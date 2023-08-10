# Define the SPL Core root directory to be used to refer to files
# relative to the repository root.
set(SPL_CORE_ROOT_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}/..)
set(SPL_CORE_CMAKE_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})
set(SPL_CORE_PYTHON_DIRECTORY ${SPL_CORE_ROOT_DIRECTORY}/src)

# Define the current build directory (variant and build_kit specific)
set(BUILD_BINARY_DIRECTORY ${CMAKE_BINARY_DIR})
set(LINK_TARGET_NAME link)
string(REPLACE "/" "_" BINARY_BASENAME ${VARIANT})

include(${CMAKE_CURRENT_LIST_DIR}/common.cmake)

if(PIP_INSTALL_REQUIREMENTS)
    run_pip("${PIP_INSTALL_REQUIREMENTS}" $ENV{SPL_PIP_REPOSITORY} $ENV{SPL_PIP_TRUSTED_HOST})
endif(PIP_INSTALL_REQUIREMENTS)

# set SPL relevant variables as environment variables, can easily be extended in CMakeLists.txt of project before including SPL core (used for KConfig variable expansion).
list(APPEND ENVVARS FLAVOR SUBSYSTEM VARIANT BUILD_KIT BINARY_BASENAME CMAKE_SOURCE_DIR)

foreach(ENVVAR IN LISTS ENVVARS)
    set(ENV{${ENVVAR}} "${${ENVVAR}}")
endforeach()

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

            add_custom_target(
                linker_byproducts ALL
                COMMAND CMAKE -E true
                DEPENDS ${LINKER_OUTPUT_FILE}
                BYPRODUCTS ${LINKER_BYPRODUCTS}
            )
        endif(LINKER_BYPRODUCTS_EXTENSIONS)
    endif(LINKER_OUTPUT_FILE)
elseif(BUILD_KIT STREQUAL test)
    _spl_get_google_test()
    include(CTest)
    list(APPEND CMAKE_CTEST_ARGUMENTS "--output-on-failure")

    add_custom_target(coverage)
    add_custom_target(docs)
    add_custom_target(reports)
else()
    message(FATAL_ERROR "Invalid BUILD_KIT selected!")
endif(BUILD_KIT STREQUAL prod)

# # Things to be done at the very end of configure phase as if they would be at bottom of CMakelists.txt
cmake_language(DEFER DIRECTORY ${CMAKE_SOURCE_DIR} CALL _spl_hook_end_of_configure())

function(_spl_hook_end_of_configure)
    _spl_coverage_create_overall_report()

    if(CONAN__REQUIRES OR CONAN__BUILD_REQUIRES)
    endif() # CONAN__REQUIRES
endfunction(_spl_hook_end_of_configure)

# # This is one possibility to open guiconfig of kconfiglib. VSCode task is the preferred solution
set(_CONFIGURATION_TARGET configuration.stamp)
add_custom_command(
    OUTPUT ${_CONFIGURATION_TARGET}
    COMMAND set "KCONFIG_CONFIG=${CMAKE_SOURCE_DIR}/variants/${VARIANT}/config.txt" && cd ${CMAKE_SOURCE_DIR} && guiconfig
)

add_custom_target(configuration DEPENDS ${_CONFIGURATION_TARGET})