function(checkout_git_submodules)
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
endfunction()

function(add_component component_path)
    slash_to_underscore(component_name ${component_path})
    add_subdirectory(${CMAKE_SOURCE_DIR}/${component_path})
    if(BUILD_KIT STREQUAL prod)
        target_link_libraries(${EXE_TARGET_NAME} ${component_name})
    endif()
endfunction()
