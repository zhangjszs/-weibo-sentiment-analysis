"""OpenTelemetry tracing + metrics with safe no-op default (#99).

Design rules:
- Disabled by default (``OTEL_ENABLED=0``): this module imports **no**
  opentelemetry packages at module load, and ``init_otel`` returns
  ``{"enabled": False}``. The fast gate never pays for observability.
- Enabled via env (``OTEL_ENABLED=1``): per-app Flask instrumentation
  (``FlaskInstrumentor.instrument_app`` — no global ``requests`` patching),
  OTLP HTTP exporter to ``OTEL_EXPORTER_OTLP_ENDPOINT``
  (default ``http://localhost:4318``), or ``console`` for local demos/tests.
- Missing packages while enabled: warn once and degrade to no-op instead
  of crashing startup.
- Idempotent: repeated ``init_otel`` calls reuse the first state; a second
  app is instrumented on top of the same providers.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "weibo-sentiment-analysis")

_COUNTER_ANALYZE = "weibo.sentiment.analyze.count"
_HISTOGRAM_ANALYZE_DURATION = "weibo.sentiment.analyze.duration"

_state: dict[str, Any] = {"enabled": False, "initialized": False}


def is_otel_enabled() -> bool:
    """True only when the operator explicitly opts in."""
    return os.getenv("OTEL_ENABLED", "0").strip().lower() in ("1", "true", "yes", "on")


def _endpoint() -> str:
    return os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318").strip()


def init_otel(app=None) -> dict[str, Any]:
    """Initialize tracing + metrics once; instrument *app* when given.

    Returns a small status dict (``enabled`` / ``endpoint`` / ``error``).
    Safe to call on every ``create_app``; only the first call builds the
    global providers, later calls just instrument their own app.
    """
    if _state.get("initialized"):
        if app is not None and _state.get("enabled"):
            _instrument_app(app)
        return dict(_state)

    if not is_otel_enabled():
        _state.update({"enabled": False, "initialized": True, "endpoint": None})
        return dict(_state)

    try:
        from opentelemetry import metrics, trace
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import (
            ConsoleMetricExporter,
            PeriodicExportingMetricReader,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )
    except ImportError as exc:
        logger.warning("OTel enabled but packages missing, running unobserved: %s", exc)
        _state.update({"enabled": False, "initialized": True, "error": str(exc)})
        return dict(_state)

    endpoint = _endpoint()
    resource = Resource.create({"service.name": SERVICE_NAME})

    provider = TracerProvider(resource=resource)
    if endpoint == "console":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    else:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")))
    trace.set_tracer_provider(provider)

    if endpoint == "console":
        metric_reader: PeriodicExportingMetricReader = PeriodicExportingMetricReader(
            ConsoleMetricExporter(), export_interval_millis=60_000
        )
    else:
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics"), export_interval_millis=60_000
        )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

    _state.update(
        {
            "enabled": True,
            "initialized": True,
            "endpoint": endpoint,
            "service": SERVICE_NAME,
        }
    )
    logger.info("OTel enabled: service=%s endpoint=%s", SERVICE_NAME, endpoint)

    if app is not None:
        _instrument_app(app)
    return dict(_state)


def _instrument_app(app) -> bool:
    """Attach Flask auto-instrumentation to one app object (idempotent)."""
    try:
        extensions = getattr(app, "extensions", None)
        if extensions is not None and extensions.get("otel_instrumented"):
            return True
        from opentelemetry.instrumentation.flask import FlaskInstrumentor

        FlaskInstrumentor().instrument_app(app)
        if extensions is not None:
            extensions["otel_instrumented"] = True
        return True
    except Exception as exc:  # never break request handling
        logger.warning("OTel Flask instrumentation failed: %s", exc)
        return False


def get_tracer(name: str = "weibo-sentiment"):
    """Return a tracer (no-op tracer when OTel is disabled)."""
    from opentelemetry import trace

    return trace.get_tracer(name)


def observe_sentiment_analysis(mode: str, duration_ms: float, ok: bool = True) -> None:
    """Record one sync sentiment analysis: counter + duration histogram.

    No-op unless OTel was initialized enabled. Never raises.
    """
    if not _state.get("enabled"):
        return
    try:
        from opentelemetry import metrics

        meter = metrics.get_meter("weibo-sentiment")
        counter = meter.create_counter(_COUNTER_ANALYZE, description="sync sentiment analyses")
        histogram = meter.create_histogram(
            _HISTOGRAM_ANALYZE_DURATION, unit="ms", description="sync sentiment analysis duration"
        )
        attrs = {"mode": str(mode), "ok": str(bool(ok)).lower()}
        counter.add(1, attrs)
        histogram.record(max(float(duration_ms), 0.0), attrs)
    except Exception as exc:  # observability must never break the request
        logger.debug("OTel metric record failed: %s", exc)


def otel_status() -> dict[str, Any]:
    """Current module state snapshot (for tests / diagnostics)."""
    return dict(_state)
