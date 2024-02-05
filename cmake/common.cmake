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
    cmake_parse_arguments(CREATE_COMPONENT "" "LONG_NAME;LIBRARY_TYPE" "" ${ARGN})
    # Set the default library type to OBJECT if not provided
    if(NOT CREATE_COMPONENT_LIBRARY_TYPE)
        set(CREATE_COMPONENT_LIBRARY_TYPE "OBJECT")
    endif()

    file(RELATIVE_PATH component_path ${CMAKE_SOURCE_DIR} ${CMAKE_CURRENT_LIST_DIR})
    _spl_slash_to_underscore(component_name ${component_path})

    # Add debug options based on build configuration (kit)
    if(BUILD_KIT STREQUAL test)
        # Exclude all components from the ALL target.
        # Components which have no tests shall not be automatically compiled when ALL target is executed.
        add_library(${component_name} EXCLUDE_FROM_ALL OBJECT ${SOURCES})
        target_compile_options(${component_name} PRIVATE ${VARIANT_ADDITIONAL_COMPILE_C_FLAGS} -ggdb --coverage)
    else()
        add_library(${component_name} ${CREATE_COMPONENT_LIBRARY_TYPE} ${SOURCES})
        target_compile_options(${component_name} PRIVATE ${VARIANT_ADDITIONAL_COMPILE_C_FLAGS})
    endif()

    # Collect all productive sources for later usage (e.g., in an extension)
    list(APPEND PROD_SOURCES ${SOURCES})
    set(PROD_SOURCES ${PROD_SOURCES} PARENT_SCOPE)
    message(DEBUG "Productive sources: ${PROD_SOURCES}")

    # Collect all component names for later usage (e.g., in an extension)
    list(APPEND COMPONENT_NAMES ${component_name})
    set(COMPONENT_NAMES ${COMPONENT_NAMES} PARENT_SCOPE)
    
    # Collect all component information for sphinx documentation
    #  - We need to keep track of all components and their information to be able to generate the variant reports.
    #    For the variants reports, one need to loop over all components and generate component variant specific targets.
    #  - We use json strings because the content will be written in a config.json file during configure.
    #    Also, CMake supports manipulating JSON strings. See the string(JSON ...) documentation.
    set(_component_info "{
\"name\": \"${component_name}\",
\"long_name\": \"${CREATE_COMPONENT_LONG_NAME}\",
\"path\": \"${component_path}\",
\"has_docs\": \"\",
\"docs_output_dir\": \"\",
\"has_reports\": \"\",
\"reports_output_dir\": \"\"
}")

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
        set(_component_coverage_json ${CMAKE_CURRENT_BINARY_DIR}/coverage.json)
        set(_component_docs_out_dir ${CMAKE_CURRENT_BINARY_DIR}/docs)
        set(_component_reports_out_dir ${CMAKE_CURRENT_BINARY_DIR}/reports)
        # The Sphinx source directory is ALWAYS the project root
        set(_sphinx_source_dir ${PROJECT_SOURCE_DIR})


        # Create component docs target if there is an index.rst file in the component's doc directory
        if(EXISTS ${_component_doc_file})
            file(RELATIVE_PATH _rel_component_docs_out_dir ${_sphinx_source_dir} ${_component_docs_out_dir})
            string(JSON _component_info SET "${_component_info}" docs_output_dir "\"${_rel_component_docs_out_dir}\"")
            string(JSON _component_info SET "${_component_info}" has_docs "\"True\"")
            set(_component_docs_html_out_dir ${_component_docs_out_dir}/html)

            # create the config.json file. This is exported as SPHINX_BUILD_CONFIGURATION_FILE env variable
            set(_docs_config_json ${_component_docs_out_dir}/config.json)
            file(RELATIVE_PATH _rel_component_doc_dir ${_sphinx_source_dir} ${_component_doc_dir})
            file(WRITE ${_docs_config_json} "{
                \"component_info\": ${_component_info},
                \"include_patterns\": [\"${_rel_component_doc_dir}/**\",\"${_rel_component_docs_out_dir}/**\"]
            }")

            # add the generated files as dependency to cmake configure step
            set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${_docs_config_json})
            add_custom_target(
                ${component_name}_docs
                COMMAND ${CMAKE_COMMAND} -E make_directory ${_component_docs_out_dir}
                # We do not know all dependencies for generating the docs (apart from the rst files).
                # This might cause incremental builds to not update parts of the documentation.
                # To avoid this we are using the -E option to make sphinx-build writing all files new.
                COMMAND ${CMAKE_COMMAND} -E env SPHINX_BUILD_CONFIGURATION_FILE=${_docs_config_json} AUTOCONF_JSON_FILE=${AUTOCONF_JSON} VARIANT=${VARIANT} -- sphinx-build -E -b html ${_sphinx_source_dir} ${_component_docs_html_out_dir}
                BYPRODUCTS ${_component_docs_html_out_dir}/index.html
            )

            if(TEST_SOURCES)
                file(RELATIVE_PATH _rel_component_reports_out_dir ${_sphinx_source_dir} ${_component_reports_out_dir})
                string(JSON _component_info SET "${_component_info}" reports_output_dir "\"${_rel_component_reports_out_dir}\"")
                string(JSON _component_info SET "${_component_info}" has_reports "\"True\"")
                set(_component_reports_html_out_dir ${_component_reports_out_dir}/html)

                # create the config.json file. This is exported as SPHINX_BUILD_CONFIGURATION_FILE env variable
                set(_reports_config_json ${_component_reports_out_dir}/config.json)

                # create the test specification rst file
                set(_unit_test_spec_rst ${_component_reports_out_dir}/unit_test_spec.rst)
                file(WRITE ${_unit_test_spec_rst} "
Unit Test Specification
=======================

.. needtable::
   :filter: type == 'test'
   :columns: id, title, tests, results
   :style: table

")

                # create the test results rst file
                set(_unit_test_results_rst ${_component_reports_out_dir}/unit_test_results.rst)
                file(WRITE ${_unit_test_results_rst} "
Unit Test Results
=================

.. test-report:: Unit Test Results
    :id: TEST_RESULT_${component_name}
    :file: ${_component_test_junit_xml}

")

                # create coverate rst file to be able to automatically link to the coverage/index.html
                set(_coverage_rst ${_component_reports_out_dir}/coverage.rst)
                file(WRITE ${_coverage_rst} "
Code Coverage
=============

`Report <coverage/index.html>`_

")

                # generate Doxyfile from template
                set(_component_doxyfile ${_component_reports_out_dir}/Doxyfile)
                set(DOXYGEN_PROJECT_NAME "${CREATE_COMPONENT_LONG_NAME} Documentation")
                set(DOXYGEN_OUTPUT_DIRECTORY ${_component_reports_out_dir}/doxygen)
                set(DOXYGEN_INPUT "${_component_dir}/src ${_component_dir}/test ${KCONFIG_OUT_DIR}")

                # We need to add the googletest include directory to the doxygen include path
                # to be able to resolve the TEST() macros in the test files.
                set(DOXYGEN_INCLUDE_PATH "${_sphinx_source_dir}/build/modules/googletest-src/googletest/include ${KCONFIG_OUT_DIR}")
                set(DOXYGEN_AWESOME_PATH "${_sphinx_source_dir}/doc/doxygen-awesome")
                configure_file(${_sphinx_source_dir}/doc/Doxyfile.in ${_component_doxyfile} @ONLY)
                file(RELATIVE_PATH _rel_component_doxyfile ${CMAKE_CURRENT_BINARY_DIR} ${_component_doxyfile})
                file(RELATIVE_PATH _rel_component_doxysphinx_index_rst ${_sphinx_source_dir} ${DOXYGEN_OUTPUT_DIRECTORY}/html/index)

                file(WRITE ${_reports_config_json} "{
    \"component_info\": ${_component_info},
    \"include_patterns\": [\"${_rel_component_doc_dir}/**\",\"${_rel_component_reports_out_dir}/**\"]
}")

                # add the generated files as dependency to cmake configure step
                set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${_reports_config_json} ${_unit_test_spec_rst} ${_unit_test_results_rst} ${_component_doxyfile})

                set(_cov_out_html reports/html/${_rel_component_reports_out_dir}/coverage/index.html)
                file(RELATIVE_PATH _cov_out_json ${CMAKE_CURRENT_BINARY_DIR} ${_component_coverage_json})
                # For the component report, one needs to generate the coverage/index.html inside the component report sphinx output directory.
                # This will avoid the need to copy the coverage/** directory inside the component report sphinx output directory.
                add_custom_command(
                    OUTPUT ${_cov_out_html}
                    COMMAND gcovr --root ${PROJECT_SOURCE_DIR} --add-tracefile ${_cov_out_json} --html --html-details --output ${_cov_out_html} ${GCOVR_ADDITIONAL_OPTIONS}
                    DEPENDS ${_cov_out_json}
                    COMMENT "Generating component coverage html report ${_cov_out_html} ..."
                )

                # We need to have a separate component doxygen generation target because it is required
                # by both the component and variant reports.
                add_custom_target(
                    # No OUTPUT is defined to force execution of this target every time
                    ${component_name}_doxygen
                    COMMAND ${CMAKE_COMMAND} -E make_directory ${_component_reports_out_dir}
                    COMMAND ${CMAKE_COMMAND} -E remove_directory ${DOXYGEN_OUTPUT_DIRECTORY}
                    COMMAND ${CMAKE_COMMAND} -E make_directory ${DOXYGEN_OUTPUT_DIRECTORY}
                    COMMAND doxygen ${_rel_component_doxyfile}
                )
                # No OUTPUT is defined to force execution of this target every time
                # TODO: list of dependencies is not complete
                add_custom_target(
                    ${component_name}_report
                    COMMAND ${CMAKE_COMMAND} -E make_directory ${_component_reports_out_dir}
                    COMMAND doxysphinx build ${_sphinx_source_dir} ${_component_reports_html_out_dir} ${_rel_component_doxyfile}
                    COMMAND ${CMAKE_COMMAND} -E env SPHINX_BUILD_CONFIGURATION_FILE=${_reports_config_json} AUTOCONF_JSON_FILE=${AUTOCONF_JSON} VARIANT=${VARIANT} -- sphinx-build -E -b html ${_sphinx_source_dir} ${_component_reports_html_out_dir}
                    BYPRODUCTS ${_component_reports_html_out_dir}/index.html
                    DEPENDS ${TEST_OUT_JUNIT} ${component_name}_doxygen ${_cov_out_html}
                )
            endif(TEST_SOURCES)
            # Collect all component sphinx include pattern to be used in the variant targets (docs, reports)
            list(APPEND COMPONENTS_SPHINX_INCLUDE_PATTERNS "${_rel_component_doc_dir}/**" "${_rel_component_docs_out_dir}/**" "${_rel_component_reports_out_dir}/**")
            set(COMPONENTS_SPHINX_INCLUDE_PATTERNS ${COMPONENTS_SPHINX_INCLUDE_PATTERNS} PARENT_SCOPE)
        endif(EXISTS ${_component_doc_file})
    endif(BUILD_KIT STREQUAL test)
    # Collect all component info for later usage (e.g., in an extension)
    list(APPEND COMPONENTS_INFO ${_component_info})
    set(COMPONENTS_INFO ${COMPONENTS_INFO} PARENT_SCOPE)
endmacro()

macro(_spl_create_docs_target)
    set(_docs_out_dir ${CMAKE_CURRENT_BINARY_DIR}/docs)
    set(_docs_html_out_dir ${_docs_out_dir}/html)
    set(_docs_config_json ${_docs_out_dir}/config.json)
    
    # create the config.json file. This is exported as SPHINX_BUILD_CONFIGURATION_FILE env variable
    list(JOIN COMPONENTS_INFO "," _components_info_json)
    set(_components_info_json "[${_components_info_json}]")
    list(JOIN COMPONENTS_SPHINX_INCLUDE_PATTERNS "\",\"" _components_sphinx_include_patterns_json)
    set(_components_sphinx_include_patterns_json "[\"${_components_sphinx_include_patterns_json}\"]")
    file(WRITE ${_docs_config_json} "{
    \"target\": \"docs\",
    \"include_patterns\": ${_components_sphinx_include_patterns_json},
    \"components_info\": ${_components_info_json}
}")

    # add the generated files as dependency to cmake configure step
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${_docs_config_json})
    add_custom_target(
        docs
        COMMAND ${CMAKE_COMMAND} -E make_directory ${_docs_out_dir}
        COMMAND ${CMAKE_COMMAND} -E env SPHINX_BUILD_CONFIGURATION_FILE=${_docs_config_json} AUTOCONF_JSON_FILE=${AUTOCONF_JSON} VARIANT=${VARIANT} -- sphinx-build -E -b html ${PROJECT_SOURCE_DIR} ${_docs_html_out_dir}
        BYPRODUCTS ${_docs_html_out_dir}/index.html
    )
endmacro()

macro(_spl_create_reports_target)
    set(_reports_output_dir ${CMAKE_CURRENT_BINARY_DIR}/reports)
    file(RELATIVE_PATH _rel_reports_output_dir ${PROJECT_SOURCE_DIR} ${_reports_output_dir})
    set(_reports_html_output_dir ${_reports_output_dir}/html)

    # create the config.json file. This is exported as SPHINX_BUILD_CONFIGURATION_FILE env variable
    set(_reports_config_json ${_reports_output_dir}/config.json)
    list(JOIN COMPONENTS_INFO "," _components_info_json)
    set(_components_info_json "[${_components_info_json}]")
    # Add the variant specific rst files (e.g, coverage.rst) to the include patterns
    list(APPEND COMPONENTS_SPHINX_INCLUDE_PATTERNS "${_rel_reports_output_dir}/**")
    list(JOIN COMPONENTS_SPHINX_INCLUDE_PATTERNS "\",\"" _components_sphinx_include_patterns_json)
    set(_components_sphinx_include_patterns_json "[\"${_components_sphinx_include_patterns_json}\"]")
    file(WRITE ${_reports_config_json} "{
    \"target\": \"reports\",
    \"include_patterns\": ${_components_sphinx_include_patterns_json},
    \"reports_output_dir\": \"${_rel_reports_output_dir}\",
    \"components_info\": ${_components_info_json}
}")

    # create the variant code coverage rst file
    set(_coverage_rst ${_reports_output_dir}/coverage.rst)
    file(WRITE ${_coverage_rst} "
Code Coverage
=============

`Report <coverage/index.html>`_

")

    # For every component we need to create specific coverage and doxysphinx targets to make sure
    # the output files are generated in the overall variant sphinx output directory.
    # This will avoid the need to copy all the component coverage and doxygen files from the component
    # directories to the variant directory.
    foreach(component_info ${COMPONENTS_INFO})
        string(JSON component_name GET ${component_info} name)
        string(JSON component_path GET ${component_info} path)
        string(JSON component_reports_output_dir GET ${component_info} reports_output_dir)
        if (component_reports_output_dir)
            set(_variant_component_reports_out_dir reports/html/${component_reports_output_dir})
            set(_cov_out_html ${_variant_component_reports_out_dir}/coverage/index.html)
            set(_cov_out_json ${component_path}/coverage.json)
            add_custom_command(
                OUTPUT ${_cov_out_html}
                COMMAND gcovr --root ${PROJECT_SOURCE_DIR} --add-tracefile ${_cov_out_json} --html --html-details --output ${_cov_out_html} ${GCOVR_ADDITIONAL_OPTIONS}
                DEPENDS ${_cov_out_json}
                COMMENT "Generating variant component coverage html report ${_cov_out_html} ..."
            )
            list(APPEND _components_coverage_html ${_cov_out_html})

            set(_rel_component_doxyfile ${component_path}/reports/Doxyfile)
            add_custom_target(
                ${component_name}_doxysphinx
                COMMAND ${CMAKE_COMMAND} -E make_directory ${_variant_component_reports_out_dir}
                COMMAND doxysphinx build ${PROJECT_SOURCE_DIR} ${_reports_html_output_dir} ${_rel_component_doxyfile}
                DEPENDS ${component_name}_doxygen
                COMMENT "Generating variant component doxysphinx report ${component_name}_doxysphinx ..."
            )
            list(APPEND _components_variant_doxysphinx_targets ${component_name}_doxysphinx)
        endif()
    endforeach()

    set(_cov_out_variant_html reports/html/${_rel_reports_output_dir}/coverage/index.html)
    add_custom_command(
        OUTPUT ${_cov_out_variant_html}
        COMMAND gcovr --root ${CMAKE_SOURCE_DIR} --add-tracefile \"${CMAKE_CURRENT_BINARY_DIR}/**/${COV_OUT_JSON}\" --html --html-details --output ${_cov_out_variant_html}
        DEPENDS ${GLOBAL_COMPONENTS_COVERAGE_JSON_LIST}
        COMMENT "Generating overall code coverage report ${_cov_out_variant_html} ..."
    )

    add_custom_target(
        _components_variant_coverage_html_target
        DEPENDS ${_components_coverage_html} ${_cov_out_variant_html}
    )
    # add the generated files as dependency to cmake configure step
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${_reports_config_json})
    add_custom_target(
        reports
        ALL
        COMMAND ${CMAKE_COMMAND} -E make_directory ${_reports_output_dir}
        # We need to call sphinx-build with -E to make sure all files are regenerated.
        COMMAND ${CMAKE_COMMAND} -E env SPHINX_BUILD_CONFIGURATION_FILE=${_reports_config_json} AUTOCONF_JSON_FILE=${AUTOCONF_JSON} VARIANT=${VARIANT} -- sphinx-build -E -b html ${PROJECT_SOURCE_DIR} ${_reports_html_output_dir}
        BYPRODUCTS ${_reports_html_output_dir}/index.html
        DEPENDS _components_variant_coverage_html_target ${_components_variant_doxysphinx_targets}
    )
endmacro()

macro(_spl_set_coverage_create_overall_report_is_necessary)
    set(_SPL_COVERAGE_CREATE_OVERALL_REPORT_IS_NECESSARY TRUE PARENT_SCOPE)
endmacro(_spl_set_coverage_create_overall_report_is_necessary)

set(COV_OUT_JSON coverage.json)

function(_spl_coverage_create_overall_report)
    if(_SPL_COVERAGE_CREATE_OVERALL_REPORT_IS_NECESSARY)
        set(COV_OUT_VARIANT_HTML reports/coverage/index.html)
        add_custom_command(
            OUTPUT ${COV_OUT_VARIANT_HTML}
            COMMAND gcovr --root ${CMAKE_SOURCE_DIR} --add-tracefile \"${CMAKE_CURRENT_BINARY_DIR}/**/${COV_OUT_JSON}\" --html --html-details --output ${COV_OUT_VARIANT_HTML}
            DEPENDS ${GLOBAL_COMPONENTS_COVERAGE_JSON_LIST}
            COMMENT "Generating overall code coverage report ${COV_OUT_VARIANT_HTML} ..."
        )
        add_custom_target(
            unittests
            DEPENDS coverage ${COV_OUT_VARIANT_HTML}
        )
        add_custom_target(
            coverage_overall_report
            DEPENDS ${COV_OUT_VARIANT_HTML}
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

    # Create JUnit report
    set(TEST_OUT_JUNIT junit.xml)
    add_custom_command(
        OUTPUT ${TEST_OUT_JUNIT}

        # Wipe all gcda files before the test executable recreates them
        COMMAND python ${SPL_CORE_PYTHON_DIRECTORY}/gcov_maid/gcov_maid.py --working-dir . --wipe-all-gcda

        # Run the test executable, generate JUnit report and return 0 independent of the test result
        COMMAND ${CMAKE_CTEST_COMMAND} ${CMAKE_CTEST_ARGUMENTS} --output-junit ${TEST_OUT_JUNIT} || ${CMAKE_COMMAND} -E true
        DEPENDS ${exe_name}
    )

    set(GLOBAL_COMPONENTS_COVERAGE_JSON_LIST "${GLOBAL_COMPONENTS_COVERAGE_JSON_LIST};${CMAKE_CURRENT_BINARY_DIR}/${COV_OUT_JSON}" CACHE INTERNAL "List of all ${COV_OUT_JSON} files")

    # Create coverage report
    add_custom_command(
        OUTPUT ${COV_OUT_JSON}

        # Wipe orphaned gcno files before gcovr searches for them
        COMMAND python ${SPL_CORE_PYTHON_DIRECTORY}/gcov_maid/gcov_maid.py --working-dir . --wipe-orphaned-gcno

        # Run gcovr to generate coverage json for the component
        COMMAND gcovr --root ${CMAKE_SOURCE_DIR} --json --output ${COV_OUT_JSON} ${GCOVR_ADDITIONAL_OPTIONS} ${CMAKE_CURRENT_BINARY_DIR}
        DEPENDS ${TEST_OUT_JUNIT}
        COMMENT "Generating component ${component_name} code coverage json report ${COV_OUT_JSON} ..."
    )

    set(COV_OUT_HTML reports/coverage/index.html)
    add_custom_command(
        OUTPUT ${COV_OUT_HTML}
        COMMAND gcovr --root ${CMAKE_SOURCE_DIR} --add-tracefile ${COV_OUT_JSON} --html --html-details --output ${COV_OUT_HTML} ${GCOVR_ADDITIONAL_OPTIONS}
        DEPENDS ${COV_OUT_JSON}
        COMMENT "Generating component ${component_name} code coverage html report ${COV_OUT_HTML} ..."
    )

    add_custom_target(
        ${component_name}_coverage
        DEPENDS ${COV_OUT_HTML}
    )
    add_custom_target(
        ${component_name}_unittests
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
