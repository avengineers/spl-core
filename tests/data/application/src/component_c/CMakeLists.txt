# Create component using data types from <stdint.h> to check if hammocking correctly finds the headers
spl_add_source(src/component_c.c)
spl_add_test_source(test/test_component_c.cc)
spl_create_component(LONG_NAME "ComponentC")
