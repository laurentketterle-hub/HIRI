"""hiri-bridge CLI - List and manage HIRI adapters."""
import argparse
import json
import sys
from pathlib import Path


def get_adapters_dir() -> Path:
    """Get the adapters directory path."""
    bridge_dir = Path(__file__).resolve().parent
    adapters_dir = bridge_dir / "adapters"
    return adapters_dir


def list_adapters(args):
    """List available adapters with optional filters."""
    adapters_dir = get_adapters_dir()

    if not adapters_dir.exists():
        print(json.dumps({"adapters": [], "error": "No adapters directory found"}))
        return

    adapters = []
    for entry in sorted(adapters_dir.iterdir()):
        if entry.is_dir() and not entry.name.startswith("_") and not entry.name.startswith("."):
            adapter_info = {
                "name": entry.name,
                "path": str(entry),
            }

            # Check for metadata
            meta_file = entry / "adapter.json"
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text())
                    adapter_info.update({
                        "version": meta.get("version", "unknown"),
                        "description": meta.get("description", ""),
                        "supported_formats": meta.get("supported_formats", []),
                    })
                except (json.JSONDecodeError, OSError):
                    pass

            adapters.append(adapter_info)

    output = {"adapters": adapters, "count": len(adapters)}
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        if not adapters:
            print("No adapters found.")
        else:
            print(f"Found {len(adapters)} adapter(s):")
            for a in adapters:
                desc = a.get("description", "")
                ver = a.get("version", "")
                info = f"  v{ver} - {desc}" if ver and desc else ""
                print(f"  - {a['name']}{info}")


def main():
    parser = argparse.ArgumentParser(
        description="hiri-bridge: List and manage HIRI adapters"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # list command
    list_parser = subparsers.add_parser("list", help="List available adapters")
    list_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )
    list_parser.set_defaults(func=list_adapters)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
