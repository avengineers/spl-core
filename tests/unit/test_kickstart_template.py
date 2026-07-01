"""Unit tests for kickstart project template conf.py consistency."""

import ast
import re
from pathlib import Path

import pytest

from spl_core.report_generation.spl_sphinx import SplSphinx

TEMPLATE_CONF_PY = Path("src/spl_core/kickstart/templates/project/conf.py")
TEMPLATE_SPHINX_DOC = Path("src/spl_core/kickstart/templates/project/doc/common/sphinx_configuration.md")


@pytest.mark.unit
class TestKickstartTemplateConsistency:
    def test_template_conf_py_references_only_existing_extension_config_keys(self):
        """Ensure conf.py only accesses keys that exist in SplSphinx.default_extension_configs."""
        source = TEMPLATE_CONF_PY.read_text(encoding="utf-8")
        # Find all extension_configs["..."] accesses
        referenced_keys = set(re.findall(r'extension_configs\["([^"]+)"\]', source))
        available_keys = set(SplSphinx.default_extension_configs.keys())
        missing = referenced_keys - available_keys
        assert missing == set(), f"conf.py references config keys not in SplSphinx.default_extension_configs: {missing}"

    def test_template_conf_py_does_not_reference_rtd(self):
        """Ensure no Read the Docs theme references remain in the template."""
        source = TEMPLATE_CONF_PY.read_text(encoding="utf-8")
        assert "sphinx_rtd" not in source, "Template still references sphinx_rtd"
        assert "rtd_theme" not in source, "Template still references rtd_theme"

    def test_template_conf_py_imports_theme_from_spl_html_settings(self):
        """Ensure the template imports html_theme from spl_html_settings."""
        source = TEMPLATE_CONF_PY.read_text(encoding="utf-8")
        assert "from spl_core.report_generation.spl_html_settings import" in source
        assert "html_theme" in source

    def test_template_conf_py_is_valid_python(self):
        """Ensure the template conf.py is syntactically valid Python."""
        source = TEMPLATE_CONF_PY.read_text(encoding="utf-8")
        # Should not raise SyntaxError
        ast.parse(source)

    def test_sphinx_configuration_doc_no_rtd_references(self):
        """Ensure the documentation does not reference RTD-specific config keys."""
        source = TEMPLATE_SPHINX_DOC.read_text(encoding="utf-8")
        assert "sphinx_rtd_size_width" not in source, "Documentation still references sphinx_rtd_size_width"
        assert "sphinx_rtd_size" not in source, "Documentation still references sphinx_rtd_size"

    def test_sphinx_configuration_doc_matches_available_keys(self):
        """Ensure code examples in docs only reference existing extension_config keys."""
        source = TEMPLATE_SPHINX_DOC.read_text(encoding="utf-8")
        referenced_keys = set(re.findall(r'extension_configs\["([^"]+)"\]', source))
        available_keys = set(SplSphinx.default_extension_configs.keys())
        missing = referenced_keys - available_keys
        assert missing == set(), f"Documentation references config keys not in SplSphinx.default_extension_configs: {missing}"
