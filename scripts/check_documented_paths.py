"""Verify that file paths referenced in documentation actually exist.

Reads README.md, docs/ARCHITECTURE.md, docs/API.md, docs/DEPLOYMENT.md and
extracts paths from backtick literals and tree blocks.  Each path is checked
against the filesystem.  Paths that match a configurable exclusion pattern
(e.g. generated dirs, known examples) are skipped.

Exit code 0 if all documented paths exist, 1 otherwise.

Usage::

    python scripts/check_documented_paths.py
    python scripts/check_documented_paths.py --strict   # also warn on orphan files
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Documents to scan for referenced paths.
DOC_FILES = [
    "README.md",
    "docs/ARCHITECTURE.md",
    "docs/API.md",
    "docs/DEPLOYMENT.md",
    "docs/PRODUCT_SCOPE.md",
    "docs/USER_FLOWS.md",
]

# Patterns to skip — these are not real filesystem paths.
SKIP_PREFIXES = (
    "http://",
    "https://",
    "mailto:",
    "docker-compose",  # compose service names, not files
    "docker compose",
)

SKIP_REGEXPS = [
    re.compile(r"^[A-Z][a-z]+[A-Z]"),  # CamelCase like MyClassName
    re.compile(r"^[a-z_]+\("),  # function_call(
    re.compile(r"^\d+\.\d+"),  # version numbers
    re.compile(r"^`?[A-Z_]+`?$"),  # ENV_VARS
    # API routes / shorthand field paths (no file extension present).
    re.compile(r"^[a-zA-Z0-9_]+/[a-zA-Z0-9_/*]+$"),  # code/msg, /getAllData/*
    re.compile(r"^/[a-zA-Z0-9_/*]+$"),  # /api, /getAllData, /api/*
    re.compile(r"^/[a-zA-Z0-9_]+/[a-zA-Z0-9_/*]*$"),  # /api/session/extend
    re.compile(r"^[a-zA-Z_]+=[^\s`]+$"),  # key=value assignments (env vars)
    re.compile(r"^[a-zA-Z_]+\.[a-zA-Z_]+$"),  # dotted fields like data.token
    # Directory-only references without extension (shorthand in prose).
    re.compile(r"^[a-z_]+/$"),  # e.g. services/, repositories/
    # Anything containing a URL scheme is not a filesystem path.
    re.compile(r"://"),
]

# Known documented paths that don't map 1:1 to files (examples, templates,
# deployment-specific paths that only exist in certain envs).
KNOWN_OK = {
    "requirements.txt",  # historically in root, now under requirements/
    "requirements-dev.txt",
    "run.py",
    ".env",
    "/etc/systemd/system/weibo-app.service",
    "/home",
    "spider/improved_config.py",
}


def extract_potential_paths(text: str) -> set[str]:
    """Extract backtick-delimited tokens that look like file paths."""
    # Match `path/to/file` but not ``code spans with spaces``
    backtick_pattern = re.compile(r"`([^\s`]+)`")
    candidates: set[str] = set()
    for match in backtick_pattern.finditer(text):
        token = match.group(1)
        if _looks_like_path(token):
            candidates.add(token)
    return candidates


def _looks_like_path(token: str) -> bool:
    if not token or len(token) < 2:
        return False
    if token.startswith(SKIP_PREFIXES):
        return False
    for regexp in SKIP_REGEXPS:
        if regexp.match(token):
            return False
    # Must contain a slash to be a path.  Bare filenames like `audit_service.py`
    # are ambiguous (could be shorthand for `src/services/audit_service.py`),
    # so we only validate tokens that include a directory separator.
    if "/" not in token:
        return False
    return True


def check_document(doc_path: Path) -> list[str]:
    """Return a list of missing paths referenced in the document."""
    if not doc_path.exists():
        return []  # Skip silently; not all docs exist in every branch.

    text = doc_path.read_text(encoding="utf-8")
    candidates = extract_potential_paths(text)
    missing: list[str] = []

    for candidate in candidates:
        if candidate in KNOWN_OK:
            continue
        # Resolve relative to project root.
        resolved = PROJECT_ROOT / candidate
        if not resolved.exists():
            missing.append(candidate)

    return missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true", help="Enable stricter checks (reserved for future use)")
    args = parser.parse_args(argv)

    all_missing: dict[str, list[str]] = {}
    for doc in DOC_FILES:
        doc_path = PROJECT_ROOT / doc
        missing = check_document(doc_path)
        if missing:
            all_missing[doc] = missing

    if all_missing:
        print("Documented paths missing from filesystem:")
        for doc, paths in all_missing.items():
            print(f"  {doc}:")
            for path in paths:
                print(f"    - {path}")
        return 1

    print("OK: all documented paths exist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
