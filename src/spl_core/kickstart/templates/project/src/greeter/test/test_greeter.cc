/**
 * @file
 */
#include <gtest/gtest.h>

extern "C" {
    #include "greeter.h"
    #include "autoconf.h"
}

#if defined(CONFIG_LANG_DE) && CONFIG_LANG_DE == 1
const char *greeting = "Hallo, Welt!";
#else
const char *greeting = "Hello, world!";
#endif
/*!
* @rst
*
* .. test:: greeter.test_get_greeting
*    :id: TS_GREETER-001
*    :tests: SWDD_GREETER-001
*
* @endrst
*/
TEST(greeter, test_get_greeting) {
    EXPECT_STREQ(greeting, get_greeting());
}
