macro(_spl_slash_to_underscore out in)
    string(REGEX REPLACE "/" "_" ${out} ${in})
endmacro()

macro(_spl_get_absolute_path out in)
    if(IS_ABSOLUTE ${in})
        cmake_path(CONVERT ${in} TO_CMAKE_PATH_LIST ${out} NORMALIZE)
    else()
        cmake_path(CONVERT ${CMAKE_CURRENT_LIST_DIR}/${in} TO_CMAKE_PATH_LIST ${out} NORMALIZE)
    endif()
endmacro()

macro(spl_add_component component_path)
    message(DEBUG "spl_add_component: component_path=${component_path}")
    _spl_slash_to_underscore(component_name ${component_path})
    add_subdirectory(${CMAKE_SOURCE_DIR}/${component_path})

    if(BUILD_KIT STREQUAL prod)
        target_link_libraries(${LINK_TARGET_NAME} ${component_name})
    endif()
endmacro()

macro(spl_add_source fileName)
    message(DEBUG "spl_add_source: fileName=${fileName}")
    cmake_parse_arguments(ADD_SOURCE_ARGS "" "" "COMPILE_OPTIONS" ${ARGN})
    _spl_get_absolute_path(to_be_appended ${fileName})
    list(APPEND SOURCES ${to_be_appended})

    if(ADD_SOURCE_ARGS_COMPILE_OPTIONS)
        message(DEBUG "spl_add_source: ADD_SOURCE_ARGS_COMPILE_OPTIONS=${ADD_SOURCE_ARGS_COMPILE_OPTIONS}")
        set_source_files_properties(${to_be_appended} PROPERTIES COMPILE_OPTIONS "${ADD_SOURCE_ARGS_COMPILE_OPTIONS}")
    endif()
endmacro()

macro(spl_add_compile_options pattern)
    message(DEBUG "spl_add_compile_options: pattern=${pattern}")
    cmake_parse_arguments(ADD_SOURCE_ARGS "" "" "COMPILE_OPTIONS" ${ARGN})
    message(DEBUG "spl_add_source: ADD_SOURCE_ARGS_COMPILE_OPTIONS=${ADD_SOURCE_ARGS_COMPILE_OPTIONS}")

    file(GLOB_RECURSE files ${CMAKE_CURRENT_LIST_DIR}/${pattern})
    message(DEBUG "spl_add_compile_options: files=${files}")

    if(files)
        foreach(file ${files})
            set_source_files_properties(${file} PROPERTIES COMPILE_OPTIONS "${ADD_SOURCE_ARGS_COMPILE_OPTIONS}")
        endforeach()
    endif()
endmacro()

macro(spl_add_include includeDirectory)
    _spl_get_absolute_path(to_be_appended ${includeDirectory})
    list(APPEND INCLUDES ${to_be_appended})
endmacro()

macro(spl_add_test_source fileName)
    _spl_get_absolute_path(to_be_appended ${fileName})
    list(APPEND TEST_SOURCES ${to_be_appended})
endmacro()

macro(_spl_get_google_test)
    # GoogleTest requires at least C++14
    set(CMAKE_CXX_STANDARD 14)

    # Make source of googletest configurable
    if(NOT DEFINED SPL_GTEST_URL)
        set(SPL_GTEST_URL https://github.com/google/googletest.git)
    endif(NOT DEFINED SPL_GTEST_URL)

    if(NOT DEFINED SPL_GTEST_TAG)
        set(SPL_GTEST_TAG v1.14.0)
    endif(NOT DEFINED SPL_GTEST_TAG)

    include(FetchContent)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY ${SPL_GTEST_URL}
        GIT_TAG ${SPL_GTEST_TAG}
    )

    # Prevent overriding the parent project's compiler/linker settings on Windows
    if(WIN32)
        set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    endif()

    # The Python version we want to use is in the PATH, so disable any search for it.
    # Got it from here: https://stackoverflow.com/questions/73514630/make-cmake-not-search-for-python-components-on-reconfigure
    set(CMAKE_DISABLE_FIND_PACKAGE_Python TRUE)

    FetchContent_MakeAvailable(googletest)
    include(GoogleTest)

    enable_testing()
endmacro(_spl_get_google_test)

macro(spl_create_component)
    file(RELATIVE_PATH component_path ${CMAKE_SOURCE_DIR} ${CMAKE_CURRENT_LIST_DIR})
    _spl_slash_to_underscore(component_name ${component_path})
    add_library(${component_name} OBJECT ${SOURCES})

    # Add debug options based on build configuration (kit)
    if(BUILD_KIT STREQUAL test)
        target_compile_options(${component_name} PRIVATE ${VARIANT_ADDITIONAL_COMPILE_C_FLAGS} -ggdb --coverage)
    else()
        target_compile_options(${component_name} PRIVATE ${VARIANT_ADDITIONAL_COMPILE_C_FLAGS})
    endif()

    list(APPEND COMPONENT_NAMES ${component_name})
    set(COMPONENT_NAMES ${COMPONENT_NAMES} PARENT_SCOPE)

    list(APPEND target_include_directories__INCLUDES ${CMAKE_CURRENT_LIST_DIR}/src)
    list(APPEND target_include_directories__INCLUDES ${CMAKE_CURRENT_BINARY_DIR})

    list(APPEND target_include_directories__INCLUDES ${INCLUDES})
    list(REMOVE_DUPLICATES target_include_directories__INCLUDES)
    set(target_include_directories__INCLUDES ${target_include_directories__INCLUDES} PARENT_SCOPE)

    if(BUILD_KIT STREQUAL test)
        # Create component unittests target
        if(TEST_SOURCES)
            set(exe_name ${component_name}_test)
            _spl_add_test_suite("${SOURCES}" ${TEST_SOURCES})
        endif()

        set(_component_dir ${CMAKE_CURRENT_LIST_DIR})
        set(_component_doc_dir ${_component_dir}/doc)
        set(_component_doc_file ${_component_doc_dir}/index.rst)
        set(_component_test_junit_xml ${CMAKE_CURRENT_BINARY_DIR}/junit.xml)
        set(_component_reports_dir ${CMAKE_CURRENT_BINARY_DIR}/reports)
        set(_autoconf_json_file ${AUTOCONF_JSON})

        # Create component docs target if there is an index.rst file in the component's doc directory
        if(EXISTS ${_component_doc_file})
            # The Sphinx source directory is always the project root
            set(SPHINX_SOURCE_DIR ${PROJECT_SOURCE_DIR})
            set(SPHINX_OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}/docs)
            file(RELATIVE_PATH _rel_sphinx_output_dir ${SPHINX_SOURCE_DIR} ${SPHINX_OUTPUT_DIR})
            set(SPHINX_OUTPUT_HTML_DIR ${SPHINX_OUTPUT_DIR}/html)
            set(SPHINX_OUTPUT_INDEX_HTML ${SPHINX_OUTPUT_HTML_DIR}/index.html)

            # create the config.json file. This is exported as SPHINX_BUILD_CONFIGURATION_FILE env variable
            set(_docs_config_json ${SPHINX_OUTPUT_DIR}/config.json)
            file(RELATIVE_PATH _rel_component_doc_dir ${SPHINX_SOURCE_DIR} ${_component_doc_dir})
            file(WRITE ${_docs_config_json} "{
                \"generated_rst_content\": \".. toctree::\\n    :maxdepth: 2\\n\\n    /${_rel_component_doc_dir}/index\",
                \"component_doc_dir\": \"${_rel_component_doc_dir}\",
                \"include_patterns\": [\"${_rel_component_doc_dir}/**\",\"${_rel_sphinx_output_dir}/**\"]
            }")

            # add the generated files as dependency to cmake configure step
            set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${_docs_config_json})
            add_custom_target(
                ${component_name}_docs
                COMMAND ${CMAKE_COMMAND} -E make_directory ${SPHINX_OUTPUT_DIR}
                COMMAND ${CMAKE_COMMAND} -E env SPHINX_BUILD_CONFIGURATION_FILE=${_docs_config_json} AUTOCONF_JSON_FILE=${_autoconf_json_file} VARIANT=${VARIANT} -- sphinx-build -b html ${SPHINX_SOURCE_DIR} ${SPHINX_OUTPUT_HTML_DIR}
                BYPRODUCTS ${SPHINX_OUTPUT_INDEX_HTML}
            )

            add_dependencies(docs ${component_name}_docs)

            if(TEST_SOURCES)
                set(SPHINX_OUTPUT_DIR ${_component_reports_dir})
                file(RELATIVE_PATH _rel_sphinx_output_dir ${SPHINX_SOURCE_DIR} ${SPHINX_OUTPUT_DIR})
                set(SPHINX_OUTPUT_HTML_DIR ${SPHINX_OUTPUT_DIR}/html)
                set(SPHINX_OUTPUT_INDEX_HTML ${SPHINX_OUTPUT_HTML_DIR}/index.html)

                # create the config.json file. This is exported as SPHINX_BUILD_CONFIGURATION_FILE env variable
                set(_reports_config_json ${SPHINX_OUTPUT_DIR}/config.json)

                # create the test_spec.rst file
                set(_unit_test_spec_rst ${SPHINX_OUTPUT_DIR}/unit_test_spec.rst)
                file(RELATIVE_PATH _rel_unit_test_spec_rst ${SPHINX_SOURCE_DIR} ${_unit_test_spec_rst})
                file(WRITE ${_unit_test_spec_rst} "
Unit Test Specification
=======================

.. needtable::
   :filter: type == 'test'
   :columns: id, title, tests, results
   :style: table

")

                # create the unit_test_results.rst file
                set(_unit_test_results_rst ${SPHINX_OUTPUT_DIR}/unit_test_results.rst)
                file(RELATIVE_PATH _rel_unit_test_results_rst ${SPHINX_SOURCE_DIR} ${_unit_test_results_rst})
                file(WRITE ${_unit_test_results_rst} "
Unit Test Results
=================

.. test-report:: Unit Test Results
    :id: TEST_RESULT
    :file: {{ component_test_junit_xml }}

")
                set(_component_doxyfile ${SPHINX_OUTPUT_DIR}/Doxyfile)

                # generate Doxyfile from template
                set(DOXYGEN_PROJECT_NAME "Doxygen Documentation")
                set(DOXYGEN_OUTPUT_DIRECTORY ${SPHINX_OUTPUT_DIR}/doxygen)
                set(DOXYGEN_INPUT "${_component_dir}/src ${_component_dir}/test ${KCONFIG_OUT_DIR}")

                # We need to add the googletest include directory to the doxygen include path
                # to be able to resolve the TEST() macros in the test files.
                set(DOXYGEN_INCLUDE_PATH "${SPHINX_SOURCE_DIR}/build/modules/googletest-src/googletest/include ${KCONFIG_OUT_DIR}")
                set(DOXYGEN_AWESOME_PATH "${SPHINX_SOURCE_DIR}/doc/doxygen-awesome")
                configure_file(${SPHINX_SOURCE_DIR}/doc/Doxyfile.in ${_component_doxyfile} @ONLY)
                file(RELATIVE_PATH _rel_component_doxyfile ${CMAKE_CURRENT_BINARY_DIR} ${_component_doxyfile})
                file(RELATIVE_PATH _rel_component_doxysphinx_index_rst ${SPHINX_SOURCE_DIR} ${DOXYGEN_OUTPUT_DIRECTORY}/html/index)

                file(WRITE ${_reports_config_json} "{
                    \"generated_rst_content\": \".. toctree::\\n    :maxdepth: 2\\n\\n    /${_rel_component_doc_dir}/index\\n    /${_rel_unit_test_spec_rst}\\n    /${_rel_unit_test_results_rst}\\n    /${_rel_component_doxysphinx_index_rst}\",
                    \"component_doc_dir\": \"${_rel_component_doc_dir}\", 
                    \"component_test_junit_xml\": \"${_component_test_junit_xml}\",
                    \"include_patterns\": [\"${_rel_component_doc_dir}/**\",\"${_rel_sphinx_output_dir}/**\"]
                }")

                # add the generated files as dependency to cmake configure step
                set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${_reports_config_json} ${_unit_test_spec_rst} ${_unit_test_results_rst} ${_component_doxyfile})

                # No OUTPUT is defined to force execution of this target every time
                # TODO: list of dependencies is not complete
                add_custom_target(
                    ${component_name}_report
                    ALL
                    COMMAND ${CMAKE_COMMAND} -E make_directory ${SPHINX_OUTPUT_DIR}
                    COMMAND ${CMAKE_COMMAND} -E remove_directory ${SPHINX_OUTPUT_DIR}/html
                    COMMAND ${CMAKE_COMMAND} -E remove_directory ${SPHINX_OUTPUT_DIR}/doxygen
                    COMMAND ${CMAKE_COMMAND} -E make_directory ${SPHINX_OUTPUT_DIR}/doxygen
                    COMMAND doxygen ${_rel_component_doxyfile}
                    COMMAND doxysphinx build ${SPHINX_SOURCE_DIR} ${SPHINX_OUTPUT_HTML_DIR} ${_rel_component_doxyfile}
                    COMMAND ${CMAKE_COMMAND} -E env SPHINX_BUILD_CONFIGURATION_FILE=${_reports_config_json} AUTOCONF_JSON_FILE=${_autoconf_json_file} VARIANT=${VARIANT} -- sphinx-build -b html ${SPHINX_SOURCE_DIR} ${SPHINX_OUTPUT_HTML_DIR}
                    BYPRODUCTS ${SPHINX_OUTPUT_INDEX_HTML}
                    DEPENDS ${TEST_OUT_JUNIT} ${COV_OUT_HTML}
                )

                add_dependencies(reports ${component_name}_report)
            endif(TEST_SOURCES)
        endif()
    endif()
endmacro()

macro(_spl_set_coverage_create_overall_report_is_necessary)
    set(_SPL_COVERAGE_CREATE_OVERALL_REPORT_IS_NECESSARY TRUE PARENT_SCOPE)
endmacro(_spl_set_coverage_create_overall_report_is_necessary)

function(_spl_coverage_create_overall_report)
    if(_SPL_COVERAGE_CREATE_OVERALL_REPORT_IS_NECESSARY)
        set(COV_OUT_VARIANT_HTML reports/coverage/index.html)
        add_custom_command(
            OUTPUT ${COV_OUT_VARIANT_HTML}
            COMMAND gcovr --root ${CMAKE_SOURCE_DIR} --add-tracefile \"${CMAKE_CURRENT_BINARY_DIR}/**/coverage.json\" --html --html-details --output ${COV_OUT_VARIANT_HTML}
            DEPENDS coverage
        )
        add_custom_target(
            unittests
            DEPENDS coverage ${COV_OUT_VARIANT_HTML}
        )
    else(_SPL_COVERAGE_CREATE_OVERALL_REPORT_IS_NECESSARY)
        add_custom_target(unittests)
    endif(_SPL_COVERAGE_CREATE_OVERALL_REPORT_IS_NECESSARY)
endfunction(_spl_coverage_create_overall_report)

macro(_spl_add_test_suite PROD_SRC TEST_SOURCES)
    _spl_set_coverage_create_overall_report_is_necessary()

    set(PROD_PARTIAL_LINK prod_partial_${component_name}.obj)
    set(MOCK_SRC mockup_${component_name}.cc)

    add_executable(${exe_name}
        ${TEST_SOURCES}
        ${MOCK_SRC}
    )

    # Produce debugging information to be able to set breakpoints while debugging.
    target_compile_options(${exe_name} PRIVATE -ggdb)

    target_link_options(${exe_name}
        PRIVATE -ggdb --coverage
    )

    add_custom_command(
        OUTPUT ${PROD_PARTIAL_LINK}
        COMMAND ${CMAKE_CXX_COMPILER} -r -nostdlib -o ${PROD_PARTIAL_LINK} $<TARGET_OBJECTS:${component_name}>
        COMMAND_EXPAND_LISTS
        VERBATIM
        DEPENDS $<TARGET_OBJECTS:${component_name}>
    )

    set(prop "$<TARGET_PROPERTY:${component_name},INCLUDE_DIRECTORIES>")
    add_custom_command(
        OUTPUT ${MOCK_SRC}
        BYPRODUCTS mockup_${component_name}.h
        WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
        COMMAND python -m hammocking --suffix _${component_name} --sources ${PROD_SRC} --plink ${CMAKE_CURRENT_BINARY_DIR}/${PROD_PARTIAL_LINK} --outdir ${CMAKE_CURRENT_BINARY_DIR} "$<$<BOOL:${prop}>:-I$<JOIN:${prop},;-I>>" -x c
        COMMAND_EXPAND_LISTS
        VERBATIM
        DEPENDS
        ${PROD_PARTIAL_LINK}
    )

    set(TEST_OUT_JUNIT junit.xml)
    add_custom_command(
        OUTPUT ${TEST_OUT_JUNIT}
        COMMAND ${CMAKE_CTEST_COMMAND} ${CMAKE_CTEST_ARGUMENTS} --output-junit ${TEST_OUT_JUNIT} || ${CMAKE_COMMAND} -E true
        DEPENDS ${exe_name}
    )

    set(COV_OUT_JSON coverage.json)
    add_custom_command(
        OUTPUT ${COV_OUT_JSON}
        COMMAND gcovr --root ${CMAKE_SOURCE_DIR} --filter ${CMAKE_CURRENT_LIST_DIR}/src --json --output ${COV_OUT_JSON} ${GCOVR_ADDITIONAL_OPTIONS} ${CMAKE_CURRENT_BINARY_DIR}
        DEPENDS ${TEST_OUT_JUNIT}
    )

    set(COV_OUT_HTML reports/coverage/index.html)
    add_custom_command(
        OUTPUT ${COV_OUT_HTML}
        COMMAND gcovr --root ${CMAKE_SOURCE_DIR} --add-tracefile ${COV_OUT_JSON} --html --html-details --output ${COV_OUT_HTML} ${GCOVR_ADDITIONAL_OPTIONS}
        DEPENDS ${COV_OUT_JSON}
    )

    add_custom_target(
        ${component_name}_coverage
        DEPENDS ${COV_OUT_HTML}
    )
    add_custom_target(
        ${component_name}_unittests
        ALL
        DEPENDS ${component_name}_coverage
    )
    add_dependencies(coverage ${component_name}_coverage)

    target_link_libraries(${exe_name}
        ${component_name}
        GTest::gtest_main
        GTest::gmock_main
        pthread
    )

    gtest_discover_tests(${exe_name})
endmacro()

macro(spl_add_conan_requires requirement)
    list(APPEND CONAN__REQUIRES ${requirement})
endmacro(spl_add_conan_requires)

macro(spl_add_conan_build_requires requirement)
    list(APPEND CONAN__BUILD_REQUIRES ${requirement})
endmacro(spl_add_conan_build_requires)

macro(spl_add_conan_install_settings settings)
    list(APPEND CONAN_INSTALL_SETTINGS ${settings})
endmacro(spl_add_conan_install_settings)

macro(spl_run_conan)
    if(CONAN__BUILD_REQUIRES OR CONAN__REQUIRES)
        # This is the wrapper-code
        include(${SPL_CORE_CMAKE_DIRECTORY}/conan.cmake)

        # This replaces file conanfile.txt
        conan_cmake_configure(
            BUILD_REQUIRES
            ${CONAN__BUILD_REQUIRES}
            REQUIRES
            ${CONAN__REQUIRES}
            GENERATORS
            cmake_paths
            virtualrunenv
        )

        # This clones a special conan config when required
        if(DEFINED SPL_CONAN_CONFIG_URL)
            if(DEFINED SPL_CONAN_CONFIG_VERIFY_SSL)
                conan_config_install(
                    ITEM ${SPL_CONAN_CONFIG_URL}
                    VERIFY_SSL ${SPL_CONAN_CONFIG_VERIFY_SSL}
                )
            else()
                conan_config_install(
                    ITEM ${SPL_CONAN_CONFIG_URL}
                )
            endif()
        endif()

        # This replaces the call of command "conan install" on the command line
        conan_cmake_install(
            PATH_OR_REFERENCE .
            SETTINGS
            ${CONAN_INSTALL_SETTINGS}
        )
        include(${CMAKE_BINARY_DIR}/conan_paths.cmake)

        # This is the ninja hack to get paths of conan packages
        _spl_set_ninja_wrapper_as_cmake_make()
    endif()
endmacro(spl_run_conan)

macro(_spl_set_ninja_wrapper_as_cmake_make)
    set(NINJA_WRAPPER ${CMAKE_SOURCE_DIR}/build/${VARIANT}/${BUILD_KIT}/ninja_wrapper.bat)
    file(WRITE ${NINJA_WRAPPER}
        "@echo off
@call %~dp0%/activate_run.bat
@ninja %*
@call %~dp0%/deactivate_run.bat")
    set(CMAKE_MAKE_PROGRAM ${NINJA_WRAPPER} CACHE FILEPATH "Custom ninja wrapper to activate the Conan virtual environment" FORCE)
endmacro()

# deprecated
macro(add_include)
    spl_add_include(${ARGN})
endmacro()

# deprecated
macro(add_source)
    spl_add_source(${ARGN})
endmacro()

# deprecated
macro(create_component)
    spl_create_component(${ARGN})
endmacro()
