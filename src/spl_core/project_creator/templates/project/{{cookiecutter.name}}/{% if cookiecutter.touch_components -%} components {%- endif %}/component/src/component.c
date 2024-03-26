/** @file */

#include "component.h"


/*!
* @rst
*
* .. impl:: someInterfaceOfComponent
*    :id: I_001
*    :implements: S_001
*
*    This function returns the magical number
*
* @endrst
*/

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
