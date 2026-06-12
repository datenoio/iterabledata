"""
Tests for plugin system functionality.
"""

from unittest.mock import Mock, patch

import pytest

from iterable.plugins import (
    PluginRegistry,
    discover_plugins,
    get_plugin_registry,
    register_codec,
    register_database_driver,
    register_engine,
    register_format,
    register_validation_rule,
    reset_discovery,
)


class TestPluginRegistry:
    """Test PluginRegistry class."""

    def setup_method(self):
        """Create a fresh registry for each test."""
        self.registry = PluginRegistry()

    def test_register_format(self):
        """Test registering a format plugin."""
        self.registry.register_format("testformat", "test.module", "TestFormat")
        assert self.registry.get_format("testformat") == ("test.module", "TestFormat")
        assert "testformat" in self.registry.list_formats()

    def test_register_format_with_metadata(self):
        """Test registering a format plugin with metadata."""
        metadata = {"version": "1.0.0", "author": "Test Author"}
        self.registry.register_format("testformat", "test.module", "TestFormat", metadata=metadata)
        assert self.registry.get_metadata("format:testformat") == metadata

    def test_register_format_duplicate(self):
        """Test that duplicate format registration raises error."""
        self.registry.register_format("testformat", "test.module", "TestFormat")
        with pytest.raises(ValueError, match="already registered"):
            self.registry.register_format("testformat", "other.module", "OtherFormat")

    def test_register_format_override(self):
        """Test that override=True allows replacing registration."""
        self.registry.register_format("testformat", "test.module", "TestFormat")
        self.registry.register_format("testformat", "other.module", "OtherFormat", override=True)
        assert self.registry.get_format("testformat") == ("other.module", "OtherFormat")

    def test_register_codec(self):
        """Test registering a codec plugin."""
        self.registry.register_codec("testcodec", "test.module", "TestCodec")
        assert self.registry.get_codec("testcodec") == ("test.module", "TestCodec")
        assert "testcodec" in self.registry.list_codecs()

    def test_register_database_driver(self):
        """Test registering a database driver plugin."""
        self.registry.register_database_driver("testdb", "test.module", "TestDriver")
        assert self.registry.get_database_driver("testdb") == ("test.module", "TestDriver")
        assert "testdb" in self.registry.list_database_drivers()

    def test_register_validation_rule(self):
        """Test registering a validation rule plugin."""

        def validator(value):
            return True, None

        self.registry.register_validation_rule("test.rule", validator)
        assert self.registry.get_validation_rule("test.rule") == validator
        assert "test.rule" in self.registry.list_validation_rules()

    def test_register_engine(self):
        """Test registering an engine plugin."""
        self.registry.register_engine("testengine", "test.module", "TestEngine")
        assert self.registry.get_engine("testengine") == ("test.module", "TestEngine")
        assert "testengine" in self.registry.list_engines()

    def test_get_metadata(self):
        """Test getting plugin metadata."""
        metadata = {"version": "1.0.0"}
        self.registry.register_format("testformat", "test.module", "TestFormat", metadata=metadata)
        assert self.registry.get_metadata("format:testformat") == metadata
        assert self.registry.get_metadata("format:nonexistent") is None


class TestConvenienceFunctions:
    """Test convenience registration functions."""

    def setup_method(self):
        """Reset registry before each test."""
        # Get fresh registry
        registry = get_plugin_registry()
        # Clear it (for testing)
        registry._formats.clear()
        registry._codecs.clear()
        registry._database_drivers.clear()
        registry._validation_rules.clear()
        registry._engines.clear()
        registry._metadata.clear()

    def test_register_format_function(self):
        """Test register_format convenience function."""
        register_format("testformat", "test.module", "TestFormat")
        registry = get_plugin_registry()
        assert registry.get_format("testformat") == ("test.module", "TestFormat")

    def test_register_codec_function(self):
        """Test register_codec convenience function."""
        register_codec("testcodec", "test.module", "TestCodec")
        registry = get_plugin_registry()
        assert registry.get_codec("testcodec") == ("test.module", "TestCodec")

    def test_register_database_driver_function(self):
        """Test register_database_driver convenience function."""
        register_database_driver("testdb", "test.module", "TestDriver")
        registry = get_plugin_registry()
        assert registry.get_database_driver("testdb") == ("test.module", "TestDriver")

    def test_register_validation_rule_function(self):
        """Test register_validation_rule convenience function."""

        def validator(value):
            return True, None

        register_validation_rule("test.rule", validator)
        registry = get_plugin_registry()
        assert registry.get_validation_rule("test.rule") == validator

    def test_register_engine_function(self):
        """Test register_engine convenience function."""
        register_engine("testengine", "test.module", "TestEngine")
        registry = get_plugin_registry()
        assert registry.get_engine("testengine") == ("test.module", "TestEngine")


class TestPluginDiscovery:
    """Test plugin discovery via entry points."""

    def setup_method(self):
        """Reset discovery state before each test."""
        reset_discovery()
        registry = get_plugin_registry()
        registry._formats.clear()
        registry._codecs.clear()
        registry._database_drivers.clear()
        registry._validation_rules.clear()
        registry._engines.clear()

    def test_discover_plugins_no_entry_points(self):
        """Test discovery when no plugins are installed."""
        discover_plugins()
        registry = get_plugin_registry()
        # Should not raise error, just discover nothing
        assert len(registry.list_formats()) == 0

    @patch("iterable.plugins.loader.metadata")
    def test_discover_format_plugins(self, mock_metadata):
        """Test discovering format plugins via entry points."""
        # Mock entry point
        mock_entry_point = Mock()
        mock_entry_point.name = "testformat"
        mock_entry_point.value = "test.module:TestFormat"
        mock_entry_point.dist = None

        mock_metadata.entry_points.return_value = [mock_entry_point]

        discover_plugins()
        registry = get_plugin_registry()
        assert "testformat" in registry.list_formats()
        assert registry.get_format("testformat") == ("test.module", "TestFormat")

    @patch("iterable.plugins.loader.metadata")
    def test_discover_codec_plugins(self, mock_metadata):
        """Test discovering codec plugins via entry points."""
        mock_entry_point = Mock()
        mock_entry_point.name = "testcodec"
        mock_entry_point.value = "test.module:TestCodec"
        mock_entry_point.dist = None

        mock_metadata.entry_points.return_value = [mock_entry_point]

        discover_plugins()
        registry = get_plugin_registry()
        assert "testcodec" in registry.list_codecs()

    @patch("iterable.plugins.loader.metadata")
    def test_discover_plugins_error_handling(self, mock_metadata):
        """Test that plugin discovery errors don't crash."""
        # Mock entry point with invalid format
        mock_entry_point = Mock()
        mock_entry_point.name = "invalid"
        mock_entry_point.value = "invalid_format"  # Missing colon
        mock_entry_point.dist = None

        mock_metadata.entry_points.return_value = [mock_entry_point]

        # Should not raise exception
        discover_plugins()
        registry = get_plugin_registry()
        # Invalid plugin should not be registered
        assert "invalid" not in registry.list_formats()

    @patch("iterable.plugins.loader.metadata")
    def test_discover_plugins_with_metadata(self, mock_metadata):
        """Test discovering plugins with distribution metadata."""
        mock_entry_point = Mock()
        mock_entry_point.name = "testformat"
        mock_entry_point.value = "test.module:TestFormat"
        mock_dist = Mock()
        mock_dist.version = "1.0.0"
        mock_dist.name = "test-plugin"
        mock_entry_point.dist = mock_dist

        mock_metadata.entry_points.return_value = [mock_entry_point]

        discover_plugins()
        registry = get_plugin_registry()
        metadata = registry.get_metadata("format:testformat")
        assert metadata is not None
        assert metadata.get("version") == "1.0.0"
        assert metadata.get("name") == "test-plugin"


class TestPluginIntegration:
    """Test plugin system integration with existing systems."""

    def test_get_format_registry_includes_plugins(self):
        """Test that _get_format_registry includes plugin formats."""
        from iterable.helpers.detect import _get_format_registry

        # Register a test plugin
        register_format("testplugin", "test.module", "TestFormat")

        registry = _get_format_registry()
        # Should include built-in formats
        assert "csv" in registry
        # Should include plugin format
        assert "testplugin" in registry

    def test_get_codec_registry_includes_plugins(self):
        """Test that _get_codec_registry includes plugin codecs."""
        from iterable.helpers.detect import _get_codec_registry

        # Register a test plugin
        register_codec("testcodec", "test.module", "TestCodec")

        registry = _get_codec_registry()
        # Should include built-in codecs
        assert "gz" in registry
        # Should include plugin codec
        assert "testcodec" in registry

    def test_built_in_formats_take_precedence(self):
        """Test that built-in formats take precedence over plugins."""
        from iterable.helpers.detect import _get_format_registry

        # Try to register a plugin with same ID as built-in
        register_format("csv", "test.module", "TestFormat", override=True)

        registry = _get_format_registry()
        # Built-in should still be used (it's copied first)
        assert registry["csv"] == ("iterable.datatypes.csv", "CSVIterable")

    def test_plugin_formats_dont_override_built_in(self):
        """Test that plugin formats don't override built-in formats."""
        from iterable.helpers.detect import _get_format_registry

        # Register plugin with same name as built-in
        register_format("csv", "test.module", "TestFormat", override=True)

        registry = _get_format_registry()
        # Built-in should still be present
        assert registry["csv"] == ("iterable.datatypes.csv", "CSVIterable")

    def test_reset_discovery(self):
        """Test reset_discovery function."""
        discover_plugins()
        reset_discovery()
        # Should be able to discover again
        discover_plugins()
        # Should not raise error
        assert True


class TestGlobalRegistry:
    """Test global registry singleton behavior."""

    def test_get_plugin_registry_singleton(self):
        """Test that get_plugin_registry returns the same instance."""
        registry1 = get_plugin_registry()
        registry2 = get_plugin_registry()
        assert registry1 is registry2
