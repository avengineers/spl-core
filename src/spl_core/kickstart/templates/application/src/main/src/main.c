/**
 * @file main.c
 * @brief Main file for the greeter application.
 */

#include <stdio.h>
#include "greeter.h"

int main(int argc, char *argv[])
{
    printf("%s\n", get_greeting());
    return 0;
}
