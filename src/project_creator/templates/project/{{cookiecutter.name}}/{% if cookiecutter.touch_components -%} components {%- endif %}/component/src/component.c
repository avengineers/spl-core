#include "component.h"

int someInterfaceOfComponent()
{
    int result = 7; /* The most magical number. */

#ifdef THE_ANSWER
    result = THE_ANSWER;
#endif

#ifdef THE_OFFSET
    result += THE_OFFSET;
#endif

    return result;
}
