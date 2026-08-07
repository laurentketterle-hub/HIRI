"""Tests pour la CLI hiri-bridge (Issue #2)."""
from __future__ import annotations

from typer.testing import CliRunner

from hiri_bridge.cli import app

runner = CliRunner()


def test_version():
    """Test : hiri-bridge version affiche la version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "HIRI-bridge" in result.stdout


def test_adapters_list():
    """Test : hiri-bridge adapters list affiche les adaptateurs."""
    result = runner.invoke(app, ["adapters", "list"])
    assert result.exit_code == 0
    assert "local" in result.stdout
    assert "mqtt" in result.stdout
    assert "z2m" in result.stdout
    assert "tuya" in result.stdout
    assert "ha_rest" in result.stdout
    assert "ha_ws" in result.stdout
    assert "matter" in result.stdout


def test_adapters_import_z2m(tmp_path):
    """Test : hiri-bridge adapters import z2m fonctionne."""
    result = runner.invoke(app, ["adapters", "import", "z2m"])
    assert result.exit_code == 0
    assert "Import" in result.stdout or "import" in result.stdout.lower()


def test_adapters_import_tuya(tmp_path):
    """Test : hiri-bridge adapters import tuya fonctionne."""
    result = runner.invoke(app, ["adapters", "import", "tuya"])
    assert result.exit_code == 0


def test_adapters_import_unknown():
    """Test : adaptateur inconnu produit une erreur."""
    result = runner.invoke(app, ["adapters", "import", "nonexistent"])
    assert result.exit_code != 0


def test_devices_list():
    """Test : hiri-bridge devices list affiche les devices."""
    result = runner.invoke(app, ["devices", "list"])
    assert result.exit_code == 0


def test_devices_search(tmp_path):
    """Test : hiri-bridge devices search trouve un device."""
    result = runner.invoke(app, ["devices", "search", "light"])
    assert result.exit_code == 0


def test_devices_stats():
    """Test : hiri-bridge devices stats affiche les stats."""
    result = runner.invoke(app, ["devices", "stats"])
    assert result.exit_code == 0
    assert "total" in result.stdout


def test_ha_discovery():
    """Test : hiri-bridge ha discovery exporte les donnees."""
    result = runner.invoke(app, ["ha", "discovery"])
    assert result.exit_code == 0


def test_mqtt_publish_dry_run():
    """Test : hiri-bridge mqtt publish --dry-run fonctionne."""
    result = runner.invoke(app, ["mqtt", "publish"])
    assert result.exit_code == 0
    assert "dry_run" in result.stdout


def test_demo():
    """Test : hiri-bridge demo fonctionne."""
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0
    assert "demo" in result.stdout.lower() or "HIRI" in result.stdout
