/** @file */

#include "component.h"
#include "component_b.h"

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

sint16 someInterfaceOfComponent()
{
    sint16 result = someInterfaceOfComponentB();

#ifdef THE_ANSWER
    result = THE_ANSWER;
#endif

#ifdef THE_OFFSET
    result += THE_OFFSET;
#endif

    return result;
}
