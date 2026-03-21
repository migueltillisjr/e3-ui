#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml  # PyYAML
except ImportError:
    print("This script requires PyYAML. Install with:  pip install pyyaml", file=sys.stderr)
    sys.exit(1)


PORT_RE = re.compile(r"(?m)(--target_port\s+)(\d+)")
# Replace all literal occurrences of 'app_name' (including in path segments and .app_name venv dir)
APP_LITERAL1 = "app_name"
APP_LITERAL2 = "target_port"

def validate_port(p):
    if not isinstance(p, int):
        raise ValueError("port must be an integer")
    if not (1 <= p <= 65535):
        raise ValueError("port must be between 1 and 65535")
    return p


def validate_app_name(name: str) -> str:
    # Allow letters, numbers, dashes, underscores only (safe for paths/venv names)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError(
            "app_name (app name) must contain only letters, numbers, dashes, or underscores"
        )
    return name


def main():
    ap = argparse.ArgumentParser(
        description="Update a systemd service file using a YAML config (keys: target_port, app_name)."
    )
    ap.add_argument("config", help="Path to YAML config file (must include 'target_port' and 'app_name').")
    ap.add_argument("service_file", help="Path to the .service file to update in-place.")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the would-be changes instead of writing to disk.",
    )
    ap.add_argument(
        "--output",
        help="Optional output path. If omitted, the input service file is overwritten (unless --dry-run).",
    )
    args = ap.parse_args()

    cfg_path = Path(args.config)
    svc_path = Path(args.service_file)

    if not cfg_path.is_file():
        print(f"Config file not found: {cfg_path}", file=sys.stderr)
        sys.exit(1)
    if not svc_path.is_file():
        print(f"Service file not found: {svc_path}", file=sys.stderr)
        sys.exit(1)

    # Load YAML
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    if "target_port" not in cfg or "app_name" not in cfg:
        print("Config must include keys: 'target_port' and 'app_name'", file=sys.stderr)
        sys.exit(1)

    target_port = validate_port(cfg["target_port"])
    app_name = validate_app_name(str(cfg["app_name"]))

    original_text = svc_path.read_text(encoding="utf-8")

    # 1) Replace --port <number>
    def port_sub(m):
        return f"{m.group(1)}{target_port}"

    updated = PORT_RE.sub(port_sub, original_text)

    # 2) Replace literal occurrences of 'app_name' everywhere (paths, venv, WorkingDirectory, etc.)
    #    This is a simple and effective approach because the sample file uses that token consistently.
    if APP_LITERAL1 in updated:
        updated = updated.replace(APP_LITERAL1, app_name)
    else:
        print(
            "Warning: No occurrences of 'app_name' were found in the service file.",
            file=sys.stderr,
        )

    # 3) Replace literal occurrences of 'target_port' everywhere (paths, venv, WorkingDirectory, etc.)
    #    This is a simple and effective approach because the sample file uses that token consistently.
    if APP_LITERAL2 in updated:
        updated = updated.replace(APP_LITERAL2, str(target_port))
    else:
        print(
            "Warning: No occurrences of 'target_port' were found in the service file.",
            file=sys.stderr,
        )

    # If nothing changed, exit gracefully
    if updated == original_text:
        print("No changes were necessary.")
        return

    # Output handling
    if args.dry_run:
        sys.stdout.write(updated)
        return

    out_path = Path(args.output) if args.output else svc_path
    out_path.write_text(updated, encoding="utf-8")
    print(f"Updated service written to: {out_path}")


if __name__ == "__main__":
    main()
