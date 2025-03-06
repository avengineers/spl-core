# Paths for KConfig output
set(KCONFIG_OUT_DIR ${PROJECT_BINARY_DIR}/kconfig)
set(AUTOCONF_H ${KCONFIG_OUT_DIR}/autoconf.h)
set(AUTOCONF_JSON ${KCONFIG_OUT_DIR}/autoconf.json)
set(AUTOCONF_CMAKE ${KCONFIG_OUT_DIR}/autoconf.cmake)
set(KCONFIG_MODEL_FILE ${PROJECT_SOURCE_DIR}/KConfig)
set(KCONFIG_CONFIG_FILE ${PROJECT_SOURCE_DIR}/variants/${VARIANT}/config.txt)

if(EXISTS ${KCONFIG_MODEL_FILE})
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${KCONFIG_MODEL_FILE})

    if(EXISTS ${KCONFIG_CONFIG_FILE})
        set(_KCONFIG_CONFIG_FILE_option --kconfig_config_file ${KCONFIG_CONFIG_FILE})
        set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${KCONFIG_CONFIG_FILE})
    else()
        message(STATUS "No variant configuration found, using defaults.")
    endif()

    # TODO: kconfig.py should not update its outputs when the inputs did not change.
    # So an incremental build with configure is not possible. autoconf.h gets updated
    # every time (although the content did not change). Therefore stuff gets compiled.
    execute_process(
        WORKING_DIRECTORY ${SPL_CORE_ROOT_DIRECTORY} # TODO: is there a better way to let kconfig.py find other modules?
        COMMAND python ${SPL_CORE_PYTHON_DIRECTORY}/kconfig/kconfig.py
        --kconfig_model_file ${KCONFIG_MODEL_FILE} ${_KCONFIG_CONFIG_FILE_option}
        --out_header_file ${AUTOCONF_H}
        --out_json_file ${AUTOCONF_JSON}
        --out_cmake_file ${AUTOCONF_CMAKE}
        COMMAND_ECHO STDOUT
        RESULT_VARIABLE ret
    )

    if(NOT "${ret}" STREQUAL "0")
        message(FATAL_ERROR "KConfig failed with return code: ${ret}")
    endif()

    # Make the generated files location public
    include_directories(${KCONFIG_OUT_DIR})
else()
    message(STATUS "No KConfig feature model file found, skipping KConfig.")
endif()
