"""MASTER CLI entry point."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("Usage: master <command> [options]")
        return 2
    if args[0] == "certification":
        from cli.certification import main as certification_main

        return certification_main(args[1:])
    print(f"[MASTER ENGINE] Unknown command: {args[0]}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
