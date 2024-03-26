/** @file */

#include <gtest/gtest.h>
using namespace testing;

extern "C"
{
#include "component.h"
}

#include "mockup_components_component.h"

/*! \mainpage
 *
 * TODO: table of tests
 */


/*!
* @rst
*
* .. test:: component.test_someInterfaceOfComponent
*    :id: T_001
*    :tests: S_001, S_002
*    :results: [[tr_link('title', 'case')]]
*
*    Some test specification
*
* @endrst
*/
TEST(component, test_someInterfaceOfComponent)
{
    /* mock all external dependencies of component */
    CREATE_MOCK(mymock);

    /* test interface */
    EXPECT_EQ(7, someInterfaceOfComponent());
}


/*!
* @rst
*
* .. test:: component.test_someInterfaceOfComponent2
*    :id: T_002
*    :tests: S_001
*    :results: [[tr_link('title', 'case')]]
*
*    Some test specification 2
*
* @endrst
*/
TEST(component, test_someInterfaceOfComponent2)
{
    /* mock all external dependencies of component */
    CREATE_MOCK(mymock);

    /* test interface */
    EXPECT_EQ(7, someInterfaceOfComponent());
}