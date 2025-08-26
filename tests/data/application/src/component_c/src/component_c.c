#include "component_c.h"

// extern void my_external_function(const uint8_t *value);

uint8_t component_c_main(void)
{
    uint8_t value = 42;
    my_external_function(&value);
    return value;
}
