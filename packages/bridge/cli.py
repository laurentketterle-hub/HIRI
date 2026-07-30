"""HIRI Bridge CLI — adapter management commands."""

import argparse
import json
from .adapters import list_adapters, get_adapter, ADAPTERS

def cmd_adapters_list(args):
    """List all available bridge adapters."""
    adapters = list_adapters()
    if args.json:
        print(json.dumps(adapters, indent=2))
        return

    print(f"{'ID':<10} {'Name':<25} {'Protocol':<12} {'Status':<10}")
    print("-" * 60)
    for a in adapters:
        print(f"{a['id']:<10} {a['name']:<25} {a['protocol']:<12} {a['status']:<10}")
    print(f"\n{len(adapters)} adapter(s) available")


def cmd_adapters_show(args):
    """Show adapter details."""
    adapter = get_adapter(args.adapter_id)
    if not adapter:
        print(f"Adapter '{args.adapter_id}' not found.")
        print(f"Available: {', '.join(ADAPTERS.keys())}")
        return

    print(f"Adapter: {adapter['name']}")
    print(f"  ID:          {args.adapter_id}")
    print(f"  Protocol:    {adapter['protocol']}")
    print(f"  Port:        {adapter['port']}")
    print(f"  Status:      {adapter['status']}")
    print(f"  Description: {adapter['description']}")


def main():
    parser = argparse.ArgumentParser(description="HIRI Bridge CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # adapters list
    list_parser = subparsers.add_parser("list", help="List available adapters")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.set_defaults(func=cmd_adapters_list)

    # adapters show
    show_parser = subparsers.add_parser("show", help="Show adapter details")
    show_parser.add_argument("adapter_id", help="Adapter ID (local/mqtt/ha_rest/z2m)")
    show_parser.set_defaults(func=cmd_adapters_show)

    # Default to list if no subcommand
    args = parser.parse_args()
    if not args.command:
        args.func = cmd_adapters_list
        args.json = False

    args.func(args)


if __name__ == "__main__":
    main()
