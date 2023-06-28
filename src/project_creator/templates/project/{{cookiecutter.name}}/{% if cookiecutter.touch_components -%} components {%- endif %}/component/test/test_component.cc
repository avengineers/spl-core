#include <gtest/gtest.h>
using namespace testing;

extern "C"
{
#include "component.h"
}

#include "mockup_components_component.h"

TEST(component, test_someInterfaceOfComponent)
{
    /* mock all external dependencies of component */
    CREATE_MOCK(mymock);

    /* test interface */
    EXPECT_EQ(7, someInterfaceOfComponent());
}
