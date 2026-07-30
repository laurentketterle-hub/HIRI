"""Tests for HIRI bridge adapters CLI."""

import sys
import os
import json
import io
from unittest.mock import patch

# Add packages/bridge to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'bridge'))

from adapters import list_adapters, get_adapter, ADAPTERS


class TestAdapters:
    """Test adapter registry."""

    def test_all_adapters_registered(self):
        """All 4 adapters should be registered."""
        assert len(ADAPTERS) == 4
        assert "local" in ADAPTERS
        assert "mqtt" in ADAPTERS
        assert "ha_rest" in ADAPTERS
        assert "z2m" in ADAPTERS

    def test_list_adapters_returns_all(self):
        """list_adapters() should return all 4."""
        adapters = list_adapters()
        assert len(adapters) == 4
        ids = {a["id"] for a in adapters}
        assert ids == {"local", "mqtt", "ha_rest", "z2m"}

    def test_list_adapters_fields(self):
        """Each adapter should have required fields."""
        for a in list_adapters():
            assert "id" in a
            assert "name" in a
            assert "protocol" in a
            assert "status" in a

    def test_get_adapter_valid(self):
        """get_adapter with valid ID returns details."""
        ad = get_adapter("local")
        assert ad is not None
        assert ad["name"] == "Local Bridge"
        assert ad["protocol"] == "HTTP/REST"

    def test_get_adapter_invalid(self):
        """get_adapter with invalid ID returns None."""
        assert get_adapter("nonexistent") is None

    def test_adapter_protocols(self):
        """Verify correct protocols."""
        assert ADAPTERS["local"]["protocol"] == "HTTP/REST"
        assert ADAPTERS["mqtt"]["protocol"] == "MQTT"
        assert ADAPTERS["ha_rest"]["protocol"] == "HTTP/REST"
        assert ADAPTERS["z2m"]["protocol"] == "MQTT"


class TestCLI:
    """Test CLI commands."""

    def test_cli_list_text_output(self):
        """CLI list should print table."""
        from cli import cmd_adapters_list
        import argparse
        ns = argparse.Namespace(json=False)
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            cmd_adapters_list(ns)
            output = fake_out.getvalue()
        assert "local" in output
        assert "MQTT Bridge" in output
        assert "4 adapter(s)" in output

    def test_cli_list_json_output(self):
        """CLI list --json should output JSON array."""
        from cli import cmd_adapters_list
        import argparse
        ns = argparse.Namespace(json=True)
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            cmd_adapters_list(ns)
            output = fake_out.getvalue()
        data = json.loads(output)
        assert len(data) == 4
        assert data[0]["id"] in ("local", "mqtt", "ha_rest", "z2m")

    def test_cli_show_valid(self):
        """CLI show with valid adapter."""
        from cli import cmd_adapters_show
        import argparse
        ns = argparse.Namespace(adapter_id="mqtt")
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            cmd_adapters_show(ns)
            output = fake_out.getvalue()
        assert "MQTT Bridge" in output
        assert "mqtt" in output

    def test_cli_show_invalid(self):
        """CLI show with invalid adapter."""
        from cli import cmd_adapters_show
        import argparse
        ns = argparse.Namespace(adapter_id="bad_adapter")
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            cmd_adapters_show(ns)
            output = fake_out.getvalue()
        assert "not found" in output
