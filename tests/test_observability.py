"""Observability tests: enabled SDK path and console probe (#99, #107).

- Enabled: exercised in-process against a real SDK, with every global the SDK
  touches saved and restored by the ``otel_sdk`` fixture, plus one subprocess
  probe for the console end-to-end path.
- Default-off and degradation tests live in ``test_observability_disabled`` so
  this module stays focused on the enabled branches that #99 could only
  measure in a subprocess.

Why in-process now: the #99 suite ran the enabled path only in subprocesses, so
the main-process branch coverage of ``observability.py`` sat at 33% and the
enabled branches were never measured by the gate. The fixture below removes
the reason for that (global provider pollution) instead of accepting it.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.unit


def _obs():
    import utils.observability as obs

    return obs


# ---------------------------------------------------------------------------
# Isolation
# ---------------------------------------------------------------------------


def _bind_console_streams(out: io.StringIO) -> None:
    """Re-point the console exporters built by ``init_otel`` at *out*.

    ``ConsoleSpanExporter`` and ``ConsoleMetricExporter`` take their ``out``
    stream as a *default argument*, and default arguments are evaluated when
    the module is first imported -- not when the exporter is constructed. Under
    pytest that import usually happens inside a captured test phase, so
    pytest's own capture object is baked into every later exporter and
    ``monkeypatch``-ing ``sys.stdout`` cannot undo it. Binding the constructed
    instances instead keeps the real exporter classes and only redirects the
    sink they write the real JSON to (``export`` writes through ``self.out``).
    """
    import opentelemetry.metrics._internal as metrics_internal
    import opentelemetry.trace as otel_trace

    provider = otel_trace.get_tracer_provider()
    processors = getattr(
        getattr(provider, "_active_span_processor", None), "_span_processors", ()
    )
    for processor in processors:
        exporter = getattr(processor, "span_exporter", None)
        if exporter is not None and hasattr(exporter, "out"):
            exporter.out = out

    # Instance field, not ``_all_metric_readers``: the SDK keeps that one as a
    # process-global WeakSet used to reject a reader registered twice.
    meter_provider = metrics_internal._METER_PROVIDER
    for reader in getattr(meter_provider, "_metric_readers", ()) or ():
        exporter = getattr(reader, "_exporter", None)
        if exporter is not None and hasattr(exporter, "out"):
            exporter.out = out


@pytest.fixture
def otel_sdk(monkeypatch):
    """Install a real OTel SDK for one test, then undo every global it touched.

    ``opentelemetry.trace.set_tracer_provider`` is guarded by a process-global
    ``Once`` latch: once it has fired, no test can ever install a real provider
    again in that interpreter. That is why the #99 suite could only probe this
    path in a subprocess. The latch is a plain ``_done`` flag, so it is saved
    and reset here -- otherwise this fixture would work exactly once and every
    later test would silently get a no-op provider.

    Yields a namespace with the module and the console output stream. The
    console exporters bind their stream at *import* time (default argument), so
    ``sys.stdout`` cannot be swapped per test; instead every ``init_otel`` call
    made through the yielded module is wrapped to re-point the freshly built
    exporters at a StringIO we own and can read back.
    """
    import opentelemetry.metrics._internal as metrics_internal
    import opentelemetry.trace as otel_trace

    obs = _obs()

    saved = {
        "state": dict(obs._state),
        "tracer": otel_trace._TRACER_PROVIDER,
        "proxy_tracer": otel_trace._PROXY_TRACER_PROVIDER,
        "tracer_once": otel_trace._TRACER_PROVIDER_SET_ONCE._done,
        "meter": metrics_internal._METER_PROVIDER,
        "proxy_meter": metrics_internal._PROXY_METER_PROVIDER,
        "meter_once": metrics_internal._METER_PROVIDER_SET_ONCE._done,
    }

    out = io.StringIO()
    monkeypatch.setenv("OTEL_ENABLED", "1")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "console")
    obs._state.clear()
    obs._state.update({"enabled": False, "initialized": False})
    otel_trace._TRACER_PROVIDER_SET_ONCE._done = False
    metrics_internal._METER_PROVIDER_SET_ONCE._done = False

    real_init_otel = obs.init_otel

    def init_otel_into_owned_stream(*args, **kwargs):
        state = real_init_otel(*args, **kwargs)
        _bind_console_streams(out)
        return state

    monkeypatch.setattr(obs, "init_otel", init_otel_into_owned_stream)

    try:
        yield SimpleNamespace(obs=obs, out=out)
    finally:
        # Stop the periodic metric readers' background threads before the
        # providers are discarded, or they outlive the test.
        for provider in (otel_trace._TRACER_PROVIDER, metrics_internal._METER_PROVIDER):
            shutdown = getattr(provider, "shutdown", None)
            if callable(shutdown):
                try:
                    shutdown()
                except Exception:  # pragma: no cover - teardown best effort
                    pass
        obs._state.clear()
        obs._state.update(saved["state"])
        otel_trace._TRACER_PROVIDER = saved["tracer"]
        otel_trace._PROXY_TRACER_PROVIDER = saved["proxy_tracer"]
        otel_trace._TRACER_PROVIDER_SET_ONCE._done = saved["tracer_once"]
        metrics_internal._METER_PROVIDER = saved["meter"]
        metrics_internal._PROXY_METER_PROVIDER = saved["proxy_meter"]
        metrics_internal._METER_PROVIDER_SET_ONCE._done = saved["meter_once"]


# ---------------------------------------------------------------------------
# Console JSON helpers
# ---------------------------------------------------------------------------


def _json_objects(text: str) -> list[dict]:
    """Every top-level JSON object in *text*, pretty-printed or compact."""
    decoder = json.JSONDecoder()
    out: list[dict] = []
    index = 0
    while index < len(text):
        start = text.find("{", index)
        if start == -1:
            break
        try:
            obj, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(obj, dict):
            out.append(obj)
        index = end
    return out


def _metric_points(docs: list[dict], metric_name: str) -> list[dict]:
    """Data points recorded for *metric_name* across all resource_metrics blocks."""
    points: list[dict] = []
    for doc in docs:
        for resource in doc.get("resource_metrics", []) or []:
            for scope in resource.get("scope_metrics", []) or []:
                for metric in scope.get("metrics", []) or []:
                    if metric.get("name") != metric_name:
                        continue
                    points.extend(metric.get("data", {}).get("data_points", []) or [])
    return points


def _attr_key(point: dict) -> tuple[str, str]:
    attrs = point.get("attributes", {})
    return str(attrs.get("mode")), str(attrs.get("ok"))


# ---------------------------------------------------------------------------
# Enabled -- real SDK, isolated
# ---------------------------------------------------------------------------


def test_enabled_emits_real_span_for_request(otel_sdk) -> None:
    """A served request must produce a real SERVER span carrying a trace id."""
    from opentelemetry.trace import SpanKind

    mini = Flask("otel_span_probe")

    @mini.route("/ping")
    def ping():
        return {"pong": True}, 200

    assert otel_sdk.obs.init_otel(mini)["enabled"] is True
    assert mini.test_client().get("/ping").status_code == 200

    spans = [
        doc
        for doc in _json_objects(otel_sdk.out.getvalue())
        if "name" in doc and "/ping" in str(doc.get("name", ""))
    ]
    assert spans, "no span was exported for the request"
    assert spans[0]["context"]["trace_id"], "span carries no trace id"
    # Console JSON serializes the enum by name (SDK 1.45.1: str(SpanKind.SERVER)).
    assert spans[0]["kind"] == str(SpanKind.SERVER), "expected a SERVER span"


def test_enabled_records_metric_values_and_attributes(otel_sdk) -> None:
    """Counter must carry exact increments; histogram must carry real values.

    The periodic reader can flush more than once, so the export may repeat the
    same data points. Asserting on the *set* of recorded (mode, ok) -> value
    pairs checks the exact numbers without depending on flush count.
    """
    from opentelemetry import metrics as otel_metrics

    otel_sdk.obs.init_otel()
    otel_sdk.obs.observe_sentiment_analysis("simple", 12.5, True)
    otel_sdk.obs.observe_sentiment_analysis("smart", 3.0, False)
    otel_metrics.get_meter_provider().force_flush()

    docs = _json_objects(otel_sdk.out.getvalue())

    counts = _metric_points(docs, "weibo.sentiment.analyze.count")
    assert counts, "counter exported no data points"
    assert {point["value"] for point in counts} == {
        1
    }, "counter must add exactly 1 per call"
    assert {_attr_key(p) for p in counts} == {("simple", "true"), ("smart", "false")}

    durations = _metric_points(docs, "weibo.sentiment.analyze.duration")
    assert durations, "histogram exported no data points"
    assert {point["count"] for point in durations} == {1}
    recorded = {_attr_key(p)[0]: p["sum"] for p in durations}
    assert recorded == {"simple": 12.5, "smart": 3.0}, recorded


def test_get_tracer_exports_real_span(otel_sdk) -> None:
    """The documented ``get_tracer`` helper must produce exportable spans."""
    otel_sdk.obs.init_otel()
    with otel_sdk.obs.get_tracer("custom-work").start_as_current_span("custom-step"):
        pass

    names = {
        str(doc.get("name"))
        for doc in _json_objects(otel_sdk.out.getvalue())
        if "name" in doc
    }
    assert "custom-step" in names, names


def test_second_app_instrumented_without_losing_first(otel_sdk) -> None:
    """A second app must be instrumented on top of the same providers."""
    first, second = Flask("otel_first"), Flask("otel_second")

    def view_a():
        return {"ok": "a"}, 200

    def view_b():
        return {"ok": "b"}, 200

    first.add_url_rule("/a", view_func=view_a)
    second.add_url_rule("/b", view_func=view_b)

    assert otel_sdk.obs.init_otel(first)["enabled"] is True
    assert otel_sdk.obs.init_otel(second)["enabled"] is True

    assert first.test_client().get("/a").status_code == 200
    assert second.test_client().get("/b").status_code == 200

    names = {
        str(doc.get("name"))
        for doc in _json_objects(otel_sdk.out.getvalue())
        if "name" in doc
    }
    assert "GET /a" in names, names
    assert "GET /b" in names, names
    assert first.extensions["otel_instrumented"] is True
    assert second.extensions["otel_instrumented"] is True


def test_repeat_init_does_not_double_instrument(otel_sdk) -> None:
    """Re-calling init on the same app must not emit duplicate spans."""
    mini = Flask("otel_repeat")

    @mini.route("/ping")
    def ping():
        return {"pong": True}, 200

    otel_sdk.obs.init_otel(mini)
    otel_sdk.obs.init_otel(
        mini
    )  # already initialized -> re-instrument, must be a no-op
    otel_sdk.obs.init_otel(mini)

    assert mini.test_client().get("/ping").status_code == 200
    names = [
        str(doc.get("name"))
        for doc in _json_objects(otel_sdk.out.getvalue())
        if "/ping" in str(doc.get("name", ""))
    ]
    assert len(names) == 1, f"expected exactly one span, got {len(names)}: {names}"
    assert mini.extensions["otel_instrumented"] is True


def test_metric_failure_does_not_break_the_caller(otel_sdk, monkeypatch) -> None:
    """A metrics SDK failure must stay inside the helper, never reach callers."""
    from opentelemetry import metrics as otel_metrics

    otel_sdk.obs.init_otel()

    def explode(*args, **kwargs):
        raise RuntimeError("meter provider unavailable")

    monkeypatch.setattr(otel_metrics, "get_meter", explode)
    assert otel_sdk.obs.observe_sentiment_analysis("simple", 12.5, True) is None


def test_collector_endpoint_wires_otlp_exporters(otel_sdk, monkeypatch) -> None:
    """A collector endpoint must build OTLP exporters instead of console ones.

    Nothing is served and no metric is recorded, so building the exporters is
    the only thing that happens -- the fixture shuts the providers down before
    any batch or periodic flush could try to reach the endpoint.
    """
    import opentelemetry.metrics._internal as metrics_internal
    import opentelemetry.trace as otel_trace
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:9")
    state = otel_sdk.obs.init_otel()

    assert state["enabled"] is True
    assert state["endpoint"] == "http://127.0.0.1:9"
    processors = list(
        otel_trace.get_tracer_provider()._active_span_processor._span_processors
    )
    assert len(processors) == 1
    assert isinstance(processors[0], BatchSpanProcessor)
    assert isinstance(processors[0].span_exporter, OTLPSpanExporter)
    readers = list(metrics_internal._METER_PROVIDER._metric_readers)
    assert len(readers) == 1
    assert isinstance(readers[0]._exporter, OTLPMetricExporter)


# ---------------------------------------------------------------------------
# Console end-to-end (subprocess): real app smoke through the console exporter
# ---------------------------------------------------------------------------

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

@mini.route("/health")
def health():
    return {"status": "ok"}, 200

state = init_otel(mini)
assert state["enabled"] is True, state
with mini.test_client() as c:
    assert c.get("/ping").status_code == 200
    assert c.get("/health").status_code == 200
observe_sentiment_analysis("simple", 12.5, True)
observe_sentiment_analysis("smart", 3.0, False)
metrics.get_meter_provider().force_flush()
print("PROBE_OK")
"""


@pytest.fixture(scope="module")
def console_probe() -> subprocess.CompletedProcess:
    """Run the console probe once; #99 ran this exact code twice."""
    env = dict(os.environ)
    env["OTEL_ENABLED"] = "1"
    env["OTEL_EXPORTER_OTLP_ENDPOINT"] = "console"
    return subprocess.run(
        [sys.executable, "-c", _PROBE_CODE],
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def test_console_probe_serves_real_requests(console_probe) -> None:
    assert console_probe.returncode == 0, console_probe.stderr[-2000:]
    assert "PROBE_OK" in console_probe.stdout
    assert "/ping" in console_probe.stdout
    assert "/health" in console_probe.stdout


def test_console_probe_metrics_carry_mode_and_ok(console_probe) -> None:
    """Console exporter output is real metric JSON, not a log line."""
    assert console_probe.returncode == 0, console_probe.stderr[-2000:]
    docs = _json_objects(console_probe.stdout)
    counts = _metric_points(docs, "weibo.sentiment.analyze.count")
    assert counts, "counter exported no data points"
    assert {point["value"] for point in counts} == {1}
    assert {_attr_key(p) for p in counts} == {("simple", "true"), ("smart", "false")}
    durations = _metric_points(docs, "weibo.sentiment.analyze.duration")
    assert {_attr_key(p)[0]: p["sum"] for p in durations} == {
        "simple": 12.5,
        "smart": 3.0,
    }


def test_console_probe_spans_are_parseable_json(console_probe) -> None:
    """Console exporter emits parseable span JSON carrying a trace id."""
    docs = [doc for doc in _json_objects(console_probe.stdout) if "context" in doc]
    assert docs, "expected console-exporter span JSON objects"
    assert all(doc["context"].get("trace_id") for doc in docs)
    names = {doc.get("name") for doc in docs}
    assert "GET /ping" in names, names
