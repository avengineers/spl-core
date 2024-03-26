#include "autoconf.h"

#if CONFIG_USE_COMPONENT
#include "component.h"
#endif

#include <stdio.h>

int main(void)
{
    printf("Main program calculating ...\n");
#if CONFIG_USE_COMPONENT
    return someInterfaceOfComponent();
#else
    return 0;
#endif
}
