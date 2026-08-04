#!/usr/bin/env python3
"""Batch-add pytest markers to test files based on filename/content heuristics."""

from __future__ import annotations

import re
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent.parent / "tests"

RULES = [
    ("test_project_health.py", "api"),
    ("test_analysis_api.py", "api"),
    ("test_api_contract.py", "api"),
    ("test_api_response.py", "unit"),
    ("test_authz.py", "unit"),
    ("test_auth_jwt.py", "unit"),
    ("test_auth_service.py", "unit"),
    ("test_bigscreen_api.py", "api"),
    ("test_data_api_helpers.py", "unit"),
    ("test_data_provenance.py", "unit"),
    ("test_documented_paths.py", "unit"),
    ("test_echarts_data_queries.py", "unit"),
    ("test_legacy_cleanup.py", "unit"),
    ("test_legacy_static_assets.py", "unit"),
    ("test_page_routes.py", "api"),
    ("test_search.py", "unit"),
    ("test_search_service.py", "unit"),
    ("test_table_data_queries.py", "unit"),
    ("test_today_stats_api.py", "api"),
    ("test_config_validator.py", "unit"),
    ("test_startup_service.py", "unit"),
    ("test_startup_status_api.py", "api"),
    ("test_audit_service.py", "unit"),
    ("test_security_hardening.py", "unit"),
    ("test_cookie.py", "unit"),
    ("test_csrf_origin_check.py", "unit"),
    ("test_alert_service.py", "integration"),
    ("test_article_service.py", "unit"),
    ("test_comment_service.py", "unit"),
    ("test_notification_service.py", "unit"),
    ("test_propagation_analyzer.py", "unit"),
    ("test_chart_renderer.py", "unit"),
    ("test_sentiment_backend.py", "unit"),
    ("test_sentiment_cache.py", "unit"),
    ("test_sentiment_enhancement.py", "unit"),
    ("test_sentiment_model.py", "unit"),
    ("test_sentiment_monitor.py", "unit"),
    ("test_sentiment_monitoring.py", "unit"),
    ("test_sentiment_optimization.py", "unit"),
    ("test_sentiment_service.py", "unit"),
    ("test_sentiment_utils.py", "unit"),
    ("test_sentiment_stress.py", "slow"),
    ("benchmark_sentiment.py", "slow"),
    ("test_real_data_apis.py", "external"),
    ("test_quick_crawl.py", "external"),
    ("test_spider_service_auth.py", "unit"),
    ("test_spider_system.py", "integration"),
    ("test_spider_task_service.py", "unit"),
    ("test_nlp_task_service.py", "unit"),
    ("test_nlp_service_passthrough.py", "unit"),
    ("test_celery_spider_events.py", "integration"),
    ("test_websocket.py", "unit"),
    ("test_websocket_integration.py", "integration"),
    ("test_db.py", "integration"),
    ("test_s10_db.py", "integration"),
    ("test_s11_task_api.py", "integration"),
    ("test_model_improvements.py", "unit"),
    ("test_model_pipeline.py", "unit"),
    ("test_contextual_sentiment.py", "unit"),
    ("test_threshold.py", "unit"),
    ("test_collaboration.py", "unit"),
    ("test_task_status_service.py", "unit"),
    ("test_platform_collector.py", "unit"),
    ("test_platform_collectors.py", "unit"),
    ("test_platform_collectors_base.py", "unit"),
    ("test_zhihu_collector.py", "unit"),
    ("test_analysis_pipeline.py", "unit"),
]


def patch_file(path: Path, marker: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if f"pytest.mark.{marker}" in text:
        return False

    if text.startswith('"""') or text.startswith("'''"):
        return False

    insert = f"import pytest\n\npytestmark = pytest.mark.{marker}\n"

    if text.startswith("#!/usr/bin/env python3"):
        lines = text.splitlines(keepends=True)
        if len(lines) >= 2 and lines[1].strip().startswith('"""'):
            idx = 1
            while idx < len(lines) and not (lines[idx].strip().endswith('"""') and idx > 1):
                idx += 1
            insert_idx = idx + 1
        else:
            insert_idx = 2
        new_text = "".join(lines[:insert_idx]) + "\n" + insert + "".join(lines[insert_idx:])
    else:
        new_text = insert + text

    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    changed = 0
    for filename, marker in RULES:
        path = TESTS_DIR / filename
        if not path.exists():
            continue
        if patch_file(path, marker):
            changed += 1
            print(f"marked {filename} -> {marker}")
    print(f"\nUpdated {changed} files.")


if __name__ == "__main__":
    main()
