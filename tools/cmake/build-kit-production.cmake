add_executable(${EXE_TARGET_NAME})
add_custom_target(default DEPENDS ${EXE_TARGET_NAME})

set_target_properties(${EXE_TARGET_NAME} PROPERTIES
    OUTPUT_NAME "${FLAVOR}_${SUBSYSTEM}"
    SUFFIX ".exe"
)

if(VARIANT_LINKER_FILE)
    set_target_properties(${EXE_TARGET_NAME} PROPERTIES
        LINK_DEPENDS ${VARIANT_LINKER_FILE}
    )
endif()

target_compile_options(${EXE_TARGET_NAME} PRIVATE ${VARIANT_ADDITIONAL_LINK_FLAGS})
