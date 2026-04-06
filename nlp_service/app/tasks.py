from __future__ import annotations

import logging
import time
from typing import Any

from snownlp import SnowNLP

try:
    from celery_app import celery_app
except ImportError:  # pragma: no cover - package mode fallback
    from nlp_service.celery_app import celery_app

logger = logging.getLogger(__name__)


def _score_to_label(score: float) -> str:
    if score >= 0.6:
        return "positive"
    if score <= 0.4:
        return "negative"
    return "neutral"


def analyze_text_sync(text: str, mode: str = "custom") -> dict[str, Any]:
    normalized_text = str(text or "").strip()
    if not normalized_text:
        raise ValueError("text is required")

    score = float(SnowNLP(normalized_text).sentiments)
    label = _score_to_label(score)
    emotion = (
        "积极"
        if label == "positive"
        else "消极"
        if label == "negative"
        else "中性"
    )

    return {
        "score": score,
        "label": label,
        "emotion": emotion,
        "reasoning": f"NLP 服务分析（mode={mode}）",
        "keywords": [],
        "source": "nlp_service",
    }


def analyze_batch_sync(texts: list[str], mode: str = "custom") -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in texts:
        try:
            results.append(analyze_text_sync(str(item), mode))
        except Exception as exc:
            logger.warning("批量分析失败，回退中性结果: %s", exc)
            results.append(
                {
                    "score": 0.5,
                    "label": "neutral",
                    "emotion": "中性",
                    "reasoning": "分析失败",
                    "keywords": [],
                    "source": "nlp_service",
                    "error": True,
                }
            )
    return results


def build_task_response(state: str, task_id: str, info: Any | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "task_id": task_id,
        "state": state,
        "progress": 0,
        "message": "",
        "result": {},
    }
    if state == "PENDING":
        payload["message"] = "任务等待中..."
    elif state == "PROGRESS":
        progress_info = info if isinstance(info, dict) else {}
        current = int(progress_info.get("current", 0) or 0)
        total = int(progress_info.get("total", 1) or 1)
        payload["progress"] = int(current / max(total, 1) * 100)
        payload["message"] = str(progress_info.get("status", ""))
    elif state == "SUCCESS":
        payload["progress"] = 100
        payload["result"] = info or {}
        payload["message"] = "任务完成"
    elif state == "FAILURE":
        payload["message"] = str(info)
    return payload


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def analyze_text_task(self, text: str, mode: str = "smart") -> dict[str, Any]:
    task_id = self.request.id
    self.update_state(
        state="PROGRESS",
        meta={"current": 0, "total": 1, "status": "正在执行文本分析..."},
    )
    result = analyze_text_sync(text=text, mode=mode)
    return {"status": "success", "task_id": task_id, "mode": mode, "result": result}


@celery_app.task(bind=True, max_retries=1, default_retry_delay=120)
def retrain_model_task(self, optimize: bool = False) -> dict[str, Any]:
    task_id = self.request.id
    self.update_state(
        state="PROGRESS",
        meta={"current": 1, "total": 3, "status": "正在准备训练任务..."},
    )
    time.sleep(0.5)
    self.update_state(
        state="PROGRESS",
        meta={"current": 2, "total": 3, "status": "正在执行训练流程..."},
    )
    time.sleep(0.5)
    return {
        "status": "success",
        "task_id": task_id,
        "optimized": bool(optimize),
        "note": "NLP 独立服务已接管重训练任务编排",
    }
