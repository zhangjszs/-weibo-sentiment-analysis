"""Version-1 analysis API endpoint.

Provides a single unified endpoint for the analysis pipeline::

    GET /api/v1/analysis?topic=<keyword>&start_at=<iso>&end_at=<iso>&demo=true
"""

from __future__ import annotations

import logging
from datetime import datetime

from flask import Blueprint, request

from ._shared import API_PREFIX

from services.analysis_pipeline import AnalysisPipeline
from utils.api_response import error as api_error, ok as api_ok

logger = logging.getLogger(__name__)

v1_analysis_bp = Blueprint("v1_analysis", __name__, url_prefix=API_PREFIX + "/v1")

bp = v1_analysis_bp  # 兼容旧引用：from views.api.v1_analysis import bp


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@v1_analysis_bp.route("/analysis", methods=["GET"])
def run_analysis():
    """Execute the analysis pipeline for a topic + time range.

    Query parameters:
        topic (str):        Keyword to analyse.
        start_at (str):     ISO-8601 start datetime.
        end_at (str):       ISO-8601 end datetime.
        demo (bool):        Set to ``true`` to use demo data (default: ``false``).

    Returns an ``AnalysisSnapshot`` as JSON with a ``meta`` provenance block.
    """
    topic = request.args.get("topic", "").strip()
    if not topic:
        return api_error("topic is required", code=400), 400

    start_at = _parse_datetime(request.args.get("start_at"))
    end_at = _parse_datetime(request.args.get("end_at"))

    if start_at and end_at and start_at >= end_at:
        return api_error("start_at must be before end_at", code=400), 400

    demo = _parse_bool(request.args.get("demo"), default=False)

    try:
        pipeline = AnalysisPipeline()
        snapshot = pipeline.run(
            topic=topic,
            start_at=start_at,
            end_at=end_at,
            demo=demo,
        )
        return api_ok(snapshot.to_dict(), msg="success"), 200
    except Exception as exc:
        logger.exception("Analysis pipeline failed for topic=%s", topic)
        return api_error(f"Analysis failed: {exc}", code=500), 500