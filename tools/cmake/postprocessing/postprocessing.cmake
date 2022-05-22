add_postprocessing_step(
    ${EXE_TARGET_NAME}
    echo Hello World! This is a post-processing step that runs after target ${EXE_TARGET_NAME} has finished.
)

add_postprocessing_step(
    ${EXE_TARGET_NAME}
    python ${CMAKE_CURRENT_LIST_DIR}/deployToArtifactory.py ${FLAVOR} ${SUBSYSTEM} $<TARGET_FILE:${EXE_TARGET_NAME}>
)
