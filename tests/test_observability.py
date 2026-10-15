"""Observability tests (#99).

- Disabled (default): pure no-op, no OTel imports at module load.
- Enabled: exercised in a **subprocess** with a bare Flask mini-app and the
  console exporter, so the gate process never installs global providers
  (which would slow every later test with per-request span export).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.unit


def test_otel_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("OTEL_ENABLED", raising=False)
    import utils.observability as obs

    state = obs.init_otel()
    assert state["enabled"] is False
    assert obs.is_otel_enabled() is False
    # no-op helpers never raise
    assert obs.observe_sentiment_analysis("simple", 12.5, True) is None
    tracer = obs.get_tracer("test")
    with tracer.start_as_current_span("noop"):
        pass


def test_otel_disabled_does_not_instrument_app(monkeypatch) -> None:
    monkeypatch.delenv("OTEL_ENABLED", raising=False)
    import utils.observability as obs

    mini = Flask("otel_disabled_probe")
    state = obs.init_otel(mini)
    assert state["enabled"] is False
    assert not (getattr(mini, "extensions", {}) or {}).get("otel_instrumented", False)


def test_otel_status_snapshot_shape(monkeypatch) -> None:
    monkeypatch.delenv("OTEL_ENABLED", raising=False)
    import utils.observability as obs

    status = obs.otel_status()
    assert set(status) >= {"enabled", "initialized"}


_PROBE_CODE = """
import os, sys
sys.path.insert(0, "src")
os.environ["OTEL_ENABLED"] = "1"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "console"
from flask import Flask
from utils.observability import init_otel, observe_sentiment_analysis
from opentelemetry import metrics

mini = Flask("otel_probe")

@mini.route("/ping")
def ping():
    return {"pong": True}, 200

state = init_otel(mini)
assert state["enabled"] is True, state
with mini.test_client() as c:
    r = c.get("/ping")
    assert r.status_code == 200
observe_sentiment_analysis("simple", 12.5, True)
observe_sentiment_analysis("smart", 3.0, False)
metrics.get_meter_provider().force_flush()
print("PROBE_OK")
"""


def test_otel_enabled_end_to_end_in_subprocess() -> None:
    """Real SDK path: request span + counter/histogram via console exporter."""
    env = dict(os.environ)
    env["OTEL_ENABLED"] = "1"
    env["OTEL_EXPORTER_OTLP_ENDPOINT"] = "console"
    proc = subprocess.run(
        [sys.executable, "-c", _PROBE_CODE],
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "PROBE_OK" in proc.stdout
    # request span for the mini-app route
    assert "/ping" in proc.stdout
    # sync-analyze counter + duration histogram
    assert "weibo.sentiment.analyze.count" in proc.stdout
    assert "weibo.sentiment.analyze.duration" in proc.stdout
    # mode/ok attributes recorded
    assert "simple" in proc.stdout


def _pretty_json_blocks(stdout: str) -> list[dict]:
    """Split console-exporter pretty-printed JSON objects (brace-balanced)."""
    blocks, depth, start, in_str, esc = [], 0, None, False, False
    for i, ch in enumerate(stdout):
        if start is None:
            if ch == "{":
                start, depth = i, 1
            continue
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                blocks.append(json.loads(stdout[start : i + 1]))
                start = None
    return blocks


def test_otel_probe_output_is_span_json() -> None:
    """Console exporter emits parseable span JSON (Jaeger accepts the same)."""
    env = dict(os.environ)
    env["OTEL_ENABLED"] = "1"
    env["OTEL_EXPORTER_OTLP_ENDPOINT"] = "console"
    proc = subprocess.run(
        [sys.executable, "-c", _PROBE_CODE],
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    docs = _pretty_json_blocks(proc.stdout)
    assert docs, "expected console-exporter JSON objects"
    assert any(doc.get("name") == "GET /ping" for doc in docs if "name" in doc)
    assert any("trace_id" in str(doc.get("context", "")) for doc in docs)
