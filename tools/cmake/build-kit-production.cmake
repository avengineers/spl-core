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

string(TIMESTAMP MILLIS "%s")
string(TIMESTAMP TODAY "%Y-%m-%d")

add_custom_command(
  TARGET ${EXE_TARGET_NAME} POST_BUILD
  COMMAND curl -u ci:eyJ2ZXIiOiIyIiwidHlwIjoiSldUIiwiYWxnIjoiUlMyNTYiLCJraWQiOiJYNktmUmpWZkFaUVk2bXdYYk9Fa25KYmZmUzNoMWpLaUN4SlY3R1RIbkxrIn0.eyJleHQiOiJ7XCJyZXZvY2FibGVcIjpcInRydWVcIn0iLCJzdWIiOiJqZmFjQDAxZzNkcjc4Y3M0emZmMDViYmF2eDUwMXAxXC91c2Vyc1wvY2kiLCJzY3AiOiJhcHBsaWVkLXBlcm1pc3Npb25zXC91c2VyIiwiYXVkIjoiKkAqIiwiaXNzIjoiamZmZUAwMDAiLCJleHAiOjE2ODQ2NzMxMzMsImlhdCI6MTY1MzEzNzEzMywianRpIjoiYWQ0MGJkZmMtOGVlMi00OWE5LWE1Y2MtMmRiMzI4YmJkYWEyIn0.SUV4V7N6-PmfpVGmBrQJysqdXVnT1fZs8IKzJlce9mzk4O0TGW7GV4Ips8oiO-pPK5bBEz0pEXyTDGgLwg3ke36G4ynmdoEJyb0LJ-0vXSv3NmMvgEwZNk_GrlMVA66N-EAH2d9p4W566ONh9YpPn7IUndgLqERwIyR25d0BycK6gMlyhlw5H0MpUHYaRlQiA7yDuq-54xyW_OyKbd_86CDzjw_Fr_HW4Scf3F5NNGEhlhTKFanynGcdfbveMcY4GBusdSs15-WdTctXCmZZpzXYHJtyW6ssRgoXrIlMI-scVdKZl0mQ6GK84NsLKy-RjtOakmw20Glg5C2P3SHX9w -X PUT "https://splbinaries.jfrog.io/artifactory/spl-generic-local/${TODAY}/${FLAVOR}_${SUBSYSTEM}_${MILLIS}.exe" -T $<TARGET_FILE:${EXE_TARGET_NAME}>
  VERBATIM)