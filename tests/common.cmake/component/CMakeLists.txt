spl_add_source(${some_file})
spl_add_source(${some_other_file} COMPILE_OPTIONS "-DTHE_ANSWER=42" "-DSOME_VALUE=7")
spl_create_component()

_spl_get_absolute_path(expected_other_source_file "${some_other_file}")
set(expected_compile_options "-DTHE_ANSWER=42")
get_source_file_property(source_file_compile_options ${expected_other_source_file} COMPILE_OPTIONS)
if(NOT expected_compile_options IN_LIST source_file_compile_options)
    message(FATAL_ERROR "Failing Test case: ${expected_compile_options} not found inside ${source_file_compile_options}.")
endif()
