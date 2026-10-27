"""Fail closed when replaying audited Moldova images over concurrent commits.

Only the PHASE_B_HANDOFF.md research note is source-neutral. This helper
validates Git diff --name-only input; it never writes files or uses network.
"""
import sys

SAFE = frozenset({"countries/moldova/research/PHASE_B_HANDOFF.md"})


def validate(paths):
    for path in paths:
        if (not isinstance(path, str) or not path or path.startswith("/")
                or "\\" in path or any(part in ("", ".", "..")
                                      for part in path.split("/"))):
            raise ValueError(f"Invalid changed path: {path!r}")
        if path not in SAFE:
            raise ValueError(f"Changed atlas source/render input: {path}")


def main():
    try:
        validate([line for line in sys.stdin.read().splitlines() if line])
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print("Only source-neutral handoff note differs; safe to attempt non-force rebase")


if __name__ == "__main__":
    main()
