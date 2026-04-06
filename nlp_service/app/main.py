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
    analyze_text_task,
    build_task_response,
    retrain_model_task,
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


@app.get("/api/nlp/tasks/<task_id>/status")
def query_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    payload = build_task_response(result.state, task_id, result.info or result.result)
    if result.state == "SUCCESS":
        payload["result"] = result.result or {}
    return _ok(payload)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8091)
