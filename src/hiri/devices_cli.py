"""CLI: hiri-bridge devices list --domain filter (Closes #89).

Usage: python -m hiri.devices_cli list --domain sensor
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import defaultdict


DEVICES_DIR = Path(__file__).resolve().parent.parent.parent / "devices"


def load_devices(devices_dir: Path = DEVICES_DIR):
    """Load all device JSON files from directory."""
    devices = []
    for fpath in sorted(devices_dir.glob("*.json")):
        try:
            data = json.loads(fpath.read_text())
            data["_source"] = fpath.name
            devices.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return devices


def filter_by_domain(devices: list, domain: str) -> list:
    """Filter devices by domain (e.g., 'sensor', 'light', 'switch')."""
    if not domain:
        return devices
    return [d for d in devices if d.get("domain", "").lower() == domain.lower()]


def list_domains(devices: list) -> dict:
    """List all domains and their device counts."""
    counts = defaultdict(int)
    for d in devices:
        domain = d.get("domain", "unknown")
        counts[domain] += 1
    return dict(sorted(counts.items()))


def format_table(devices: list, columns: list[str] = None) -> str:
    """Format devices as a readable table."""
    if columns is None:
        columns = ["entity_id", "domain", "state"]

    if not devices:
        return "No devices found."

    col_widths = {c: max(len(c), max((len(str(d.get(c, ""))) for d in devices), default=0)) for c in columns}
    header = " | ".join(c.ljust(col_widths[c]) for c in columns)
    sep = "-+-".join("-" * col_widths[c] for c in columns)

    rows = [header, sep]
    for d in devices:
        row = " | ".join(str(d.get(c, "")).ljust(col_widths[c]) for c in columns)
        rows.append(row)

    rows.append("")
    rows.append("Total: {} devices".format(len(devices)))
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description="HIRI Bridge devices CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List devices with optional domain filter")
    list_parser.add_argument("--domain", type=str, help="Filter by domain (e.g., sensor, light, switch)")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    domains_parser = sub.add_parser("domains", help="List all domains with device counts")

    args = parser.parse_args()
    devices = load_devices()

    if args.command == "list":
        filtered = filter_by_domain(devices, args.domain)
        if args.json:
            print(json.dumps(filtered, indent=2))
        else:
            print(format_table(filtered))
        return 0

    elif args.command == "domains":
        domain_counts = list_domains(devices)
        for domain, count in domain_counts.items():
            print("  {} ({} devices)".format(domain, count))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
