#!/usr/bin/env python3
"""
安全加固回归测试
"""

import os
import pickle
import shutil
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def _make_test_dir(prefix: str) -> str:
    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src", "cache")
    )
    os.makedirs(base_dir, exist_ok=True)
    test_dir = os.path.join(base_dir, f"{prefix}_{uuid.uuid4().hex}")
    os.makedirs(test_dir, exist_ok=True)
    return test_dir


def test_file_cache_uses_json_and_drops_legacy_pickle():
    from utils.cache import FileCache

    temp_dir = _make_test_dir("cache_security")
    try:
        cache = FileCache(cache_dir=temp_dir, default_timeout=3600)

        payload = {"name": "demo", "count": 2, "items": ["a", "b"]}
        cache.set("json_key", payload)
        assert cache.get("json_key") == payload

        legacy_path = cache._get_cache_path("legacy_key")
        with open(legacy_path, "wb") as f:
            f.write(pickle.dumps({"legacy": True}))

        assert cache.get("legacy_key") is None
        assert not os.path.exists(legacy_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_memory_duplicate_filter_persists_plain_text(monkeypatch):
    import utils.deduplicator as dedup

    temp_dir = _make_test_dir("dedup_security")
    try:
        if dedup.Config:
            monkeypatch.setattr(dedup.Config, "CACHE_DIR", temp_dir, raising=False)

        filter_name = "unit_test"
        dedup_filter = dedup.MemoryDuplicateFilter(name=filter_name)
        dedup_filter.add("item-1")
        dedup_filter.save()

        reloaded = dedup.MemoryDuplicateFilter(name=filter_name)
        assert reloaded.is_duplicate("item-1")
        assert os.path.exists(
            os.path.join(temp_dir, f"duplicate_filter_{filter_name}.jsonl")
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_parse_ngram_range_is_safe():
    from model.hyperparameter_optimizer import parse_ngram_range

    assert parse_ngram_range("(1,2)") == (1, 2)
    assert parse_ngram_range("__import__('os').system('echo injected')") == (1, 1)


def test_config_exposes_redis_and_llm_contract():
    from config.settings import Config

    assert hasattr(Config, "REDIS_URL")
    assert hasattr(Config, "CELERY_BROKER_URL")
    assert hasattr(Config, "CELERY_RESULT_BACKEND")
    assert hasattr(Config, "LLM_API_URL")
    assert hasattr(Config, "LLM_MODEL")
    assert isinstance(Config.get_redis_connection_params(), dict)


def test_sentiment_distribution_aggregates_labels(monkeypatch):
    import services.sentiment_service as sentiment_module
    from services.sentiment_service import SentimentService

    monkeypatch.setattr(sentiment_module, "REDIS_AVAILABLE", False)

    def _fake_analyze_batch(texts, mode="simple"):
        return [
            {"label": "positive"},
            {"label": "neutral"},
            {"label": "negative"},
            {"label": "positive"},
        ]

    monkeypatch.setattr(
        SentimentService, "analyze_batch", staticmethod(_fake_analyze_batch)
    )

    result = SentimentService.analyze_distribution(
        ["a", "b", "c", "d"], mode="simple", sample_size=4
    )
    assert result == {"正面": 2, "中性": 1, "负面": 1}
