C/C++ Definitions
=================

.. _c_defines:

This is a list of all the C/C++ preprocessor definitions provided by SPL Core. These are used to control the behavior of the code at compile time.


SPLE_UNIT_TESTING
-----------------

This definition is defined for any C/C++ code being compiled for unit testing in build kit ``test``.

.. code-block:: C

 #define SPLE_UNIT_TESTING

It can be used to conditionally compile code for unit testing.


SPLE_TESTABLE_STATIC
--------------------

This definition is defined for any C/C++ code being compiled using SPL Core.

For build kit ``test``, this definition is defined to nothing to enable the testing and mocking of static functions and variables.

.. code-block:: C

 #define SPLE_TESTABLE_STATIC=

For build kit ``prod``, this definition is defined to ``static``.

.. code-block:: C

 #define SPLE_TESTABLE_STATIC=static


SPLE_TESTABLE_INLINE
--------------------

This definition is defined for any C/C++ code being compiled using SPL Core.

For build kit ``test``, this definition is defined to nothing to enable the testing and mocking of inline functions.

.. code-block:: C

 #define SPLE_TESTABLE_INLINE=

For build kit ``prod``, this definition is defined to ``inline``.

.. code-block:: C

 #define SPLE_TESTABLE_INLINE=inline
