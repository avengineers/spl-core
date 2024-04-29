/**
 * @file greeter.c
 * @brief Greeter implementation.
 */


#include "greeter.h"
#include "autoconf.h"

/*!
* @rst
*
* .. impl:: Select the greeting message
*    :id: SWIMPL_GREETER-001
*    :implements: SWDD_GREETER-001
* @endrst
*/
const char* get_greeting() {
    #if defined(CONFIG_LANG_DE) && CONFIG_LANG_DE == 1
        return "Hallo, Welt!";
    #else
        return "Hello, world!";
    #endif
}
