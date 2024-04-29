Software Detailed Design
========================

.. figure:: _images/screenshot.png

.. mermaid::

   graph TD
      A[Start] --> B{Language}
      B -->|DE| C[Hallo Welt]
      B -->|EN| D[Hello World]
      C --> E[End]
      D --> E

Requirements
------------

.. spec:: Say Hello
   :id: SWDD_GREETER-001
   :integrity: QM

{% if config.LANG_DE %}
   It shall greet the user with ``Hallo Welt``.
{% else %}
   It shall greet the user with ``Hello World``.
{% endif %}
