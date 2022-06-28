macro(slash_to_underscore out in)
    string(REGEX REPLACE "/" "_" ${out} ${in})
endmacro()

macro(get_absolute_path out in)
    string(FIND ${in} "/" position)
    if(position STREQUAL 0)
        # Assumption: path starting with '/' means relative to project root
        cmake_path(CONVERT ${PROJECT_SOURCE_DIR}/${in} TO_CMAKE_PATH_LIST ${out} NORMALIZE)
    else()
        cmake_path(CONVERT ${CMAKE_CURRENT_LIST_DIR}/${in} TO_CMAKE_PATH_LIST ${out} NORMALIZE)
    endif()
endmacro()

macro(add_source fileName)
    get_absolute_path(to_be_appended ${fileName})
    list(APPEND SOURCES ${to_be_appended})
endmacro()

macro(add_include includeDirectory)
    get_absolute_path(to_be_appended ${includeDirectory})
    list(APPEND INCLUDES ${to_be_appended})
endmacro()

macro(add_test_source fileName)
    get_absolute_path(to_be_appended ${fileName})
    list(APPEND TEST_SOURCES ${to_be_appended})
endmacro()

macro(create_mocks fileName)
    if(BUILD_KIT STREQUAL test)
        get_absolute_path(FILE_TO_BE_MOCKED ${fileName})
        cmake_path(GET FILE_TO_BE_MOCKED FILENAME FILE_BASE_NAME)
        cmake_path(REMOVE_EXTENSION FILE_BASE_NAME LAST_ONLY OUTPUT_VARIABLE FILE_BASE_NAME_WITHOUT_EXTENSION)
        file(RELATIVE_PATH component_path ${CMAKE_SOURCE_DIR} ${CMAKE_CURRENT_LIST_DIR})
        add_custom_command(OUTPUT ${PROJECT_SOURCE_DIR}/build/${VARIANT}/${BUILD_KIT}/${component_path}/mocks/mock_${FILE_BASE_NAME_WITHOUT_EXTENSION}.c
            COMMAND cmd /C "ruby ${PROJECT_SOURCE_DIR}/tools/CMock/lib/cmock.rb -o${PROJECT_SOURCE_DIR}/cmock-config.yml ${FILE_TO_BE_MOCKED}"
            DEPENDS ${PROJECT_SOURCE_DIR}/${fileName}
        )
        add_include(/build/${VARIANT}/${BUILD_KIT}/${component_path}/mocks)
        add_test_source(/build/${VARIANT}/${BUILD_KIT}/${component_path}/mocks/mock_${FILE_BASE_NAME_WITHOUT_EXTENSION}.c)
    endif()
endmacro()

macro(create_component)
    file(RELATIVE_PATH component_path ${CMAKE_SOURCE_DIR} ${CMAKE_CURRENT_LIST_DIR})
    slash_to_underscore(component_name ${component_path})
    add_library(${component_name} OBJECT ${SOURCES})
    target_compile_options(${component_name} PRIVATE ${VARIANT_ADDITIONAL_COMPILE_C_FLAGS})

    target_include_directories(${component_name} PUBLIC ${CMAKE_CURRENT_LIST_DIR}/src)
    target_include_directories(${component_name} PUBLIC ${INCLUDES})
    if((BUILD_KIT STREQUAL test) AND TEST_SOURCES)
        set(exe_name ${component_name}_test)
        add_test_suite(${TEST_SOURCES})
    endif()
endmacro()

macro(add_test_suite)
    add_executable(${exe_name}
        ${ARGN}
    )

    set(TEST_OUT_JUNIT junit.xml)
    add_custom_command( 
        OUTPUT ${TEST_OUT_JUNIT}
        COMMAND ${CMAKE_CTEST_COMMAND} ${CMAKE_CTEST_ARGUMENTS} --output-junit ${TEST_OUT_JUNIT}
        DEPENDS ${exe_name}
    )

    set(COV_OUT_JSON coverage.json)
    add_custom_command( 
        OUTPUT ${COV_OUT_JSON}
        COMMAND gcovr --root ${CMAKE_SOURCE_DIR} --filter ${CMAKE_CURRENT_LIST_DIR}/src --json --output ${COV_OUT_JSON} ${GCOVR_ADDITIONAL_OPTIONS}
        DEPENDS ${TEST_OUT_JUNIT}
    )

    set(COV_OUT_HTML coverage/index.html)
    add_custom_command( 
        OUTPUT ${COV_OUT_HTML}
        COMMAND gcovr --root ${CMAKE_SOURCE_DIR} --add-tracefile ${COV_OUT_JSON} --html --html-details --output ${COV_OUT_HTML} ${GCOVR_ADDITIONAL_OPTIONS}
        DEPENDS ${COV_OUT_JSON}
    )

    add_custom_target(${component_name}_coverage DEPENDS ${COV_OUT_HTML})
    add_custom_target(${component_name}_unittests DEPENDS ${component_name}_coverage)
    add_dependencies(coverage ${component_name}_coverage)

    target_link_libraries(${exe_name}
        ${component_name}
        CMock
    )

    add_test(${component_name}_test ${exe_name})
endmacro()

macro(checkout_git_submodules)
    #first time checkout submodules, ignore if existing
    execute_process(
        COMMAND git submodule update --init --recursive
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        ERROR_QUIET
    )

    #consecutive times just pull changes
    execute_process(
        COMMAND git submodule update --recursive
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    )
endmacro()

macro(add_component component_path)
    slash_to_underscore(component_name ${component_path})
    add_subdirectory(${CMAKE_SOURCE_DIR}/${component_path})
    if(BUILD_KIT STREQUAL prod)
        target_link_libraries(${EXE_TARGET_NAME} ${component_name})
    endif()
endmacro()
