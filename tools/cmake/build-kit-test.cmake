include(CTest)
list(APPEND CMAKE_CTEST_ARGUMENTS "--output-on-failure")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -ggdb --coverage")
add_library(Unity STATIC
    tools/Unity/src/unity.c
)

target_include_directories(Unity PUBLIC
    tools/Unity/src
)

add_library(CMock
    tools/CMock/src/cmock.c
)

target_include_directories(CMock PUBLIC 
    tools/CMock/src
)

target_link_libraries(CMock Unity)

set(COV_OUT_VARIANT_HTML coverage/index.html)

add_custom_command( 
    OUTPUT ${COV_OUT_VARIANT_HTML}
    COMMAND gcovr --root ${CMAKE_SOURCE_DIR} --add-tracefile \"${CMAKE_CURRENT_BINARY_DIR}/**/coverage.json\" --html --html-details --output ${COV_OUT_VARIANT_HTML}
    DEPENDS coverage
)
add_custom_target(coverage)
add_custom_target(unittests DEPENDS coverage ${COV_OUT_VARIANT_HTML})
