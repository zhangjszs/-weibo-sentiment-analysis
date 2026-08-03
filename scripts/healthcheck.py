"""Standalone health-check script for local use and CI smoke tests.

Runs a few HTTP checks against a running Flask app and exits with a
non-zero status when any critical check fails.  This script is intended
to be called after ``docker compose up`` or ``flask run`` to verify the
deployment before running deeper smoke tests.

Usage::

    python scripts/healthcheck.py                  # checks http://127.0.0.1:5000
    python scripts/healthcheck.py -b http://host:port
    python scripts/healthcheck.py --timeout 5

The script never imports the Flask application; it only uses ``urllib``
from the standard library so it works in minimal CI environments.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:5000"
DEFAULT_TIMEOUT_SECONDS = 10


def _get_json(base_url: str, path: str, timeout: float) -> tuple[int, dict[str, Any] | None]:
    url = base_url.rstrip("/") + path
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            try:
                return response.status, json.loads(raw)
            except (ValueError, json.JSONDecodeError):
                return response.status, None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            return exc.code, None
    except urllib.error.URLError as exc:
        return -1, {"error": f"connection failed: {exc.reason}"}
    except TimeoutError:
        return -2, {"error": "request timed out"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "-b", "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL of the running Flask app (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Per-request timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS})",
    )
    args = parser.parse_args(argv)

    base_url = args.base_url
    timeout = args.timeout
    failures: list[str] = []

    # 1. Liveness: /health must return 200 and {"status": "ok"}.
    status, body = _get_json(base_url, "/health", timeout)
    if status != 200:
        failures.append(f"/health returned HTTP {status} (expected 200)")
    elif not isinstance(body, dict) or body.get("status") != "ok":
        failures.append(f"/health body missing status=ok: {body!r}")

    # 2. Readiness: /ready must return JSON with a "checks" map.
    status, body = _get_json(base_url, "/ready", timeout)
    if status not in {200, 503}:
        failures.append(f"/ready returned HTTP {status} (expected 200 or 503)")
    elif not isinstance(body, dict) or "checks" not in body:
        failures.append(f"/ready body missing 'checks': {body!r}")
    elif status == 503:
        # 503 is acceptable in environments without MySQL/Redis, but we
        # surface it so the caller knows the app is not fully ready.
        check_names = sorted(body.get("checks", {}).keys())
        print(f"info: /ready reports 503 (checks: {check_names})")

    if failures:
        print("healthcheck FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("healthcheck OK: /health and /ready are responding correctly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
