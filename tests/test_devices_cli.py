"""Tests for devices filter --domain CLI (Closes #89)."""
import json
import tempfile
from pathlib import Path
from src.hiri.devices_cli import load_devices, filter_by_domain, list_domains, format_table


SAMPLE_DEVICES_DIR = Path(__file__).parent / "fixtures" / "devices"


class TestFilterByDomain:
    def make_device(self, entity_id, domain, state="on"):
        return {"entity_id": entity_id, "domain": domain, "state": state}

    def test_filter_matching_domain(self):
        devices = [
            self.make_device("sensor.temp", "sensor"),
            self.make_device("light.kitchen", "light"),
            self.make_device("sensor.humidity", "sensor"),
        ]
        filtered = filter_by_domain(devices, "sensor")
        assert len(filtered) == 2
        assert all(d["domain"] == "sensor" for d in filtered)

    def test_filter_case_insensitive(self):
        devices = [self.make_device("light.kitchen", "Light")]
        filtered = filter_by_domain(devices, "light")
        assert len(filtered) == 1

    def test_filter_no_match(self):
        devices = [self.make_device("switch.a", "switch")]
        filtered = filter_by_domain(devices, "sensor")
        assert len(filtered) == 0

    def test_filter_empty_domain_returns_all(self):
        devices = [self.make_device("a", "x"), self.make_device("b", "y")]
        filtered = filter_by_domain(devices, "")
        assert len(filtered) == 2


class TestListDomains:
    def test_counts_by_domain(self):
        devices = [
            {"entity_id": "a", "domain": "light"},
            {"entity_id": "b", "domain": "light"},
            {"entity_id": "c", "domain": "sensor"},
        ]
        counts = list_domains(devices)
        assert counts["light"] == 2
        assert counts["sensor"] == 1

    def test_unknown_domain(self):
        devices = [{"entity_id": "x"}]
        counts = list_domains(devices)
        assert counts["unknown"] == 1


class TestFormatTable:
    def test_non_empty_table(self):
        devices = [{"entity_id": "light.a", "domain": "light", "state": "on"}]
        table = format_table(devices)
        assert "light.a" in table
        assert "1 devices" in table

    def test_empty_table(self):
        table = format_table([])
        assert "No devices" in table
