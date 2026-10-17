"""Observability tests: default-off and degradation paths (#99, #107).

Split from ``test_observability.py`` to keep each module focused: the enabled
in-process behaviour and the console probe live there. Everything here asserts
*absence of effect* or failure containment, not status-dict shapes.
"""

from __future__ import annotations

import sys

import pytest
from flask import Flask

pytestmark = pytest.mark.unit


def _obs():
    import utils.observability as obs

    return obs


# ---------------------------------------------------------------------------
# Disabled (default) -- absence of effect, not status-dict shape
# ---------------------------------------------------------------------------


def test_disabled_installs_no_sdk_provider(monkeypatch) -> None:
    """Default-off must leave the OTel globals as untouched as before."""
    import opentelemetry.metrics._internal as metrics_internal
    import opentelemetry.trace as otel_trace

    monkeypatch.delenv("OTEL_ENABLED", raising=False)
    obs = _obs()

    assert obs.init_otel(Flask("disabled_probe"))["enabled"] is False
    # No real SDK provider was installed, so spans/metrics cannot be exported.
    assert otel_trace._TRACER_PROVIDER is None
    assert metrics_internal._METER_PROVIDER is None


def test_disabled_app_is_not_instrumented(monkeypatch) -> None:
    monkeypatch.delenv("OTEL_ENABLED", raising=False)
    obs = _obs()

    mini = Flask("otel_disabled_probe")
    obs.init_otel(mini)
    assert not (getattr(mini, "extensions", {}) or {}).get("otel_instrumented", False)

    # The app still serves requests, and records nothing.
    @mini.route("/ping")
    def ping():
        return {"pong": True}, 200

    assert mini.test_client().get("/ping").status_code == 200


def test_disabled_observe_is_a_noop(monkeypatch) -> None:
    """Metrics helper must be inert when disabled (not merely non-raising)."""
    monkeypatch.delenv("OTEL_ENABLED", raising=False)
    obs = _obs()
    obs.init_otel()

    import opentelemetry.metrics._internal as metrics_internal

    obs.observe_sentiment_analysis("simple", 12.5, True)
    assert (
        metrics_internal._METER_PROVIDER is None
    ), "disabled path created a meter provider"


# ---------------------------------------------------------------------------
# Degradation -- observability failures must not break the request
# ---------------------------------------------------------------------------


def test_missing_packages_degrades_and_app_still_serves(monkeypatch, caplog) -> None:
    """Enabled but packages missing: warn, record, keep serving."""
    monkeypatch.setenv("OTEL_ENABLED", "1")
    # Classic import blocker: a None entry makes `import x` raise ImportError.
    # We block a module observability needs *without* touching observability
    # itself, so the degradation branch under test is the real one.
    monkeypatch.setitem(sys.modules, "opentelemetry.sdk.trace", None)

    obs = _obs()
    saved = dict(obs._state)
    obs._state.clear()
    obs._state.update({"enabled": False, "initialized": False})
    try:
        state = obs.init_otel()
    finally:
        obs._state.clear()
        obs._state.update(saved)

    assert state["enabled"] is False
    assert state["error"], "degradation must record why it fell back"
    assert any("packages missing" in r.getMessage() for r in caplog.records)

    mini = Flask("otel_missing_pkgs")

    @mini.route("/ping")
    def ping():
        return {"pong": True}, 200

    assert mini.test_client().get("/ping").status_code == 200


def test_instrumentation_failure_does_not_break_requests(monkeypatch) -> None:
    """A bad app object must degrade to "not instrumented", not raise."""
    import opentelemetry.metrics._internal as metrics_internal
    import opentelemetry.trace as otel_trace

    monkeypatch.setenv("OTEL_ENABLED", "1")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "console")

    obs = _obs()
    saved = dict(obs._state)
    obs._state.clear()
    obs._state.update({"enabled": False, "initialized": False})
    otel_trace._TRACER_PROVIDER_SET_ONCE._done = False
    metrics_internal._METER_PROVIDER_SET_ONCE._done = False
    try:
        # Not a Flask app: FlaskInstrumentor refuses it, and init_otel must
        # still return a usable state instead of propagating.
        state = obs.init_otel(object())
    finally:
        obs._state.clear()
        obs._state.update(saved)
        otel_trace._TRACER_PROVIDER = None
        metrics_internal._METER_PROVIDER = None

    assert state["enabled"] is True
    assert obs._state["initialized"] is True


# ---------------------------------------------------------------------------
# Endpoint parsing
# ---------------------------------------------------------------------------


def test_endpoint_default_is_localhost(monkeypatch) -> None:
    """Unset endpoint falls back to the documented collector address."""
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    assert _obs()._endpoint() == "http://localhost:4318"


def test_endpoint_is_read_from_env(monkeypatch) -> None:
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", " http://collector:4318 ")
    assert _obs()._endpoint() == "http://collector:4318"
