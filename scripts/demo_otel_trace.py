#!/usr/bin/env python3
"""OTel live demo against the real app with the console exporter (#99).

Usage:
    OTEL_ENABLED=1 OTEL_EXPORTER_OTLP_ENDPOINT=console \
        .venv/bin/python scripts/demo_otel_trace.py

Hits public routes (/health, /ready) through the Flask test client and
prints the spans the SDK exports. Point OTEL_EXPORTER_OTLP_ENDPOINT at
Jaeger/collector for the UI version (see docs/OBSERVABILITY.md).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

os.environ.setdefault("TEST_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "disabled")
os.environ.setdefault("AUTO_CREATE_DEMO_ADMIN", "False")
os.environ.setdefault("SECRET_KEY", "demo-secret-key-must-be-at-least-32-chars")
os.environ.setdefault("JWT_SECRET_KEY", "demo-jwt-secret-key-must-be-at-least-32-ch")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault("ADMIN_USERS", "admin")
os.environ.setdefault("OTEL_ENABLED", "1")
os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "console")

from app import create_app  # noqa: E402
from utils.observability import otel_status  # noqa: E402


def main() -> int:
    app = create_app()
    print("otel_status:", otel_status())
    with app.test_client() as client:
        for path in ("/health", "/ready"):
            resp = client.get(path)
            print(f"GET {path} -> {resp.status_code}")
    from opentelemetry import metrics  # noqa: E402

    metrics.get_meter_provider().force_flush()
    print("DEMO_DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
