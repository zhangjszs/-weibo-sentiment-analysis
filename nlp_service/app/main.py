from __future__ import annotations

import os

from celery.result import AsyncResult
from flask import Flask, jsonify, request

try:
    from celery_app import celery_app
except ImportError:  # pragma: no cover - package mode fallback
    from nlp_service.celery_app import celery_app

from app.tasks import (
    analyze_batch_sync,
    analyze_text_sync,
    analyze_sequence_sync,
    analyze_text_task,
    analyze_sequence_task,
    build_task_response,
    retrain_model_task,
    update_dictionary,
    get_dictionary_stats,
)

app = Flask(__name__)


def _ok(data: dict, code: int = 200):
    return jsonify({"code": code, "msg": "ok", "data": data}), code


def _error(message: str, code: int = 400):
    return jsonify({"code": code, "msg": message, "data": {}}), code


def _unauthorized_if_needed():
    token = os.getenv("NLP_SERVICE_TOKEN", "").strip()
    if not token or request.path == "/health":
        return None
    auth_header = request.headers.get("Authorization", "").strip()
    if auth_header != f"Bearer {token}":
        return _error("unauthorized", 401)
    return None


@app.before_request
def _check_auth():
    return _unauthorized_if_needed()


@app.get("/health")
def health():
    return _ok({"status": "ok"})


@app.post("/api/nlp/analyze")
def analyze_text():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    mode = str(payload.get("mode", "custom")).strip() or "custom"
    if not text:
        return _error("text is required", 400)

    try:
        if mode == "auto":
            from app.sentiment_strategy_selector import AdaptiveStrategyManager
            manager = AdaptiveStrategyManager()
            result = manager.analyze(text)
        else:
            result = analyze_text_sync(text=text, mode=mode)
        return _ok(result)
    except Exception as exc:
        return _error(str(exc), 500)


@app.post("/api/nlp/predict/batch")
def analyze_batch():
    payload = request.get_json(silent=True) or {}
    texts = payload.get("texts", [])
    mode = str(payload.get("mode", "custom")).strip() or "custom"
    if not isinstance(texts, list) or not texts:
        return _error("texts 必须是非空数组", 400)
    if len(texts) > 100:
        return _error("单次最多预测100条文本", 400)

    try:
        if mode == "auto":
            from app.sentiment_strategy_selector import AdaptiveStrategyManager
            manager = AdaptiveStrategyManager()
            results = manager.analyze_batch([str(item) for item in texts])
        else:
            results = analyze_batch_sync([str(item) for item in texts], mode=mode)
        return _ok({"total": len(results), "results": results})
    except Exception as exc:
        return _error(str(exc), 500)


@app.post("/api/nlp/tasks/analyze")
def submit_analyze_task():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    mode = str(payload.get("mode", "smart")).strip() or "smart"
    if not text:
        return _error("text is required", 400)

    task = analyze_text_task.delay(text=text, mode=mode)
    return _ok(
        {
            "task_id": task.id,
            "task_label": "情感分析",
            "mode": mode,
            "status": "PENDING",
        }
    )


@app.post("/api/nlp/tasks/retrain")
def submit_retrain_task():
    payload = request.get_json(silent=True) or {}
    optimize = bool(payload.get("optimize", False))
    task = retrain_model_task.delay(optimize=optimize)
    return _ok(
        {
            "task_id": task.id,
            "task_label": "模型重训练",
            "mode": "custom",
            "status": "PENDING",
        }
    )


@app.post("/api/nlp/analyze/sequence")
def analyze_sequence():
    payload = request.get_json(silent=True) or {}
    texts = payload.get("texts", [])
    mode = str(payload.get("mode", "custom")).strip() or "custom"
    if not isinstance(texts, list) or not texts:
        return _error("texts 必须是非空数组", 400)
    if len(texts) > 50:
        return _error("单次最多分析50条文本序列", 400)

    try:
        result = analyze_sequence_sync([str(item) for item in texts], mode=mode)
        return _ok(result)
    except Exception as exc:
        return _error(str(exc), 500)


@app.post("/api/nlp/tasks/analyze/sequence")
def submit_analyze_sequence_task():
    payload = request.get_json(silent=True) or {}
    texts = payload.get("texts", [])
    mode = str(payload.get("mode", "custom")).strip() or "custom"
    if not isinstance(texts, list) or not texts:
        return _error("texts 必须是非空数组", 400)
    if len(texts) > 100:
        return _error("单次最多分析100条文本序列", 400)

    task = analyze_sequence_task.delay(texts=texts, mode=mode)
    return _ok(
        {
            "task_id": task.id,
            "task_label": "序列情感分析",
            "mode": mode,
            "status": "PENDING",
        }
    )


@app.get("/api/nlp/dictionary/stats")
def get_dictionary_statistics():
    """
    获取词典统计信息
    """
    try:
        stats = get_dictionary_stats()
        return _ok(stats)
    except Exception as exc:
        return _error(str(exc), 500)


@app.post("/api/nlp/dictionary/update")
def update_dictionary_api():
    """
    更新情感词典
    """
    payload = request.get_json(silent=True) or {}
    positive_words = payload.get("positive_words", [])
    negative_words = payload.get("negative_words", [])
    
    if not isinstance(positive_words, list):
        positive_words = []
    if not isinstance(negative_words, list):
        negative_words = []
    
    try:
        stats = update_dictionary(positive_words, negative_words)
        return _ok(stats)
    except Exception as exc:
        return _error(str(exc), 500)


@app.get("/api/nlp/tasks/<task_id>/status")
def query_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    payload = build_task_response(result.state, task_id, result.info or result.result)
    if result.state == "SUCCESS":
        payload["result"] = result.result or {}
    return _ok(payload)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8091)
