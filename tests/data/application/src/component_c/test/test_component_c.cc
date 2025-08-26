#include <gtest/gtest.h>
using namespace testing;

extern "C"
{
#include "component_c.h"
}

#include "mockup_src_component_c.h"

TEST(component_c, test_my_internal_function)
{
    CREATE_MOCK(mymock);
    EXPECT_CALL(mymock, my_external_function(_)).Times(1).WillOnce(SetArgPointee<0>(13));
    EXPECT_EQ(13, component_c_main());
}
