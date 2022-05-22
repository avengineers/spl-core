add_postprocessing_step(
    test #build-kit: 'prod' or 'test'
    ${unittest} # target name, e.g. exe or unittest
    echo Hello World! This is a post-processing step that runs after target '${EXE_TARGET_NAME}' has finished.  # command to call
)

add_postprocessing_step(
    prod
    ${EXE_TARGET_NAME}
    python ${CMAKE_CURRENT_LIST_DIR}/deployToArtifactory.py ${FLAVOR} ${SUBSYSTEM} $<TARGET_FILE:${EXE_TARGET_NAME}>
)
