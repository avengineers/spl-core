{% if build_config.component_doc_dir %}

Software Component Report
=========================

**Variant:** {{ build_config.variant }}

.. toctree::
    :maxdepth: 2

    {{ build_config.component_doc_dir }}/index
{% if build_config.component_reports_dir %}
    {{ build_config.component_reports_dir }}/unit_test_spec
    {{ build_config.component_reports_dir }}/unit_test_results
    {{ build_config.component_reports_dir }}/doxygen/html/index
    {{ build_config.component_reports_dir }}/coverage
{% endif %}

{% else %}

Variant Report
==============

**Variant:** {{ build_config.variant }}

.. toctree::
    :maxdepth: 1
    :caption: Contents:

    doc/software_requirements/index
    doc/software_architecture/index

{% endif %}
