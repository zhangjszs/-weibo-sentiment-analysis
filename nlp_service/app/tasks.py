"""nlp_service 任务模块。

Phase 3.8 改造后，本模块不再做任何 NLP 计算，全部通过 HTTP 透传到主后端
（默认 ``http://web:5000``）的 ``/api/sentiment/analyze``、``/api/predict/batch``
与 ``/api/model/retrain`` 接口。这样做的好处是：

* 算法升级（BERT / sklearn / snownlp 降级链）集中在主后端维护，nlp_service 仅做异步编排；
* 移除 snownlp / circuitbreaker / pydantic-settings 等重复依赖，缩小镜像体积；
* 缓存、模型版本、熔断只在主后端实现一次，避免双写不一致。
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

try:
    from celery_app import celery_app
except ImportError:  # pragma: no cover - package mode fallback
    from nlp_service.celery_app import celery_app

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 主后端 HTTP 透传配置
# ---------------------------------------------------------------------------

DEFAULT_BACKEND_URL = "http://web:5000"


def _backend_url() -> str:
    """读取主后端地址，去掉末尾斜杠以方便拼接路径。"""
    url = os.getenv("NLP_BACKEND_URL", DEFAULT_BACKEND_URL).strip().rstrip("/")
    return url or DEFAULT_BACKEND_URL


def _backend_timeout() -> float:
    """单次 HTTP 透传超时时间（秒）。"""
    try:
        return float(os.getenv("NLP_BACKEND_TIMEOUT", "20"))
    except (TypeError, ValueError):
        return 20.0


def _auth_headers() -> dict[str, str]:
    """如果配置了服务间鉴权 token，则带上 Authorization 头。"""
    token = os.getenv("NLP_SERVICE_TOKEN", "").strip()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """向主后端 POST 请求并返回 ``data`` 字段。

    主后端统一返回 ``{"code": int, "msg": str, "timestamp": str, "data": ...}``，
    非成功状态码会抛 :class:`RuntimeError`，由调用方决定如何降级。
    """
    url = f"{_backend_url()}{path}"
    try:
        resp = requests.post(
            url,
            json=payload,
            headers=_auth_headers(),
            timeout=_backend_timeout(),
        )
    except requests.RequestException as exc:
        logger.error("透传主后端失败 %s: %s", url, exc)
        raise RuntimeError(f"主后端不可用: {exc}") from exc

    try:
        body = resp.json()
    except ValueError as exc:
        logger.error("主后端返回非 JSON 响应 %s: %s", url, exc)
        raise RuntimeError("主后端响应解析失败") from exc

    if resp.status_code >= 400 or body.get("code", resp.status_code) >= 400:
        msg = body.get("msg") or f"主后端返回 {resp.status_code}"
        logger.warning("透传 %s 失败: %s", path, msg)
        raise RuntimeError(msg)

    return body.get("data") or {}


# ---------------------------------------------------------------------------
# 同步透传函数
# ---------------------------------------------------------------------------


def analyze_text_sync(text: str, mode: str = "custom") -> dict[str, Any]:
    """单条文本情感分析，透传到主后端 ``/api/sentiment/analyze``。"""
    normalized = str(text or "").strip()
    if not normalized:
        raise ValueError("text is required")

    return _post(
        "/api/sentiment/analyze",
        {"text": normalized, "mode": mode, "async": False},
    )


def analyze_batch_sync(texts: list[str], mode: str = "custom") -> list[dict[str, Any]]:
    """批量文本情感分析，透传到主后端 ``/api/predict/batch``。

    主后端返回 ``{"total": int, "results": [...]}``，本函数仅返回 results 列表，
    保持与原 SnowNLP 实现一致的调用方契约。
    """
    if not isinstance(texts, list) or not texts:
        raise ValueError("texts 必须是非空数组")
    if len(texts) > 100:
        raise ValueError("单次最多预测100条文本")

    payload = {"texts": [str(item) for item in texts], "mode": mode}
    data = _post("/api/predict/batch", payload)
    results = data.get("results", []) if isinstance(data, dict) else []
    return list(results)


def analyze_sequence_sync(texts: list[str], mode: str = "custom") -> dict[str, Any]:
    """序列情感分析。

    主后端没有专门的序列接口，因此本函数对每条文本调用
    :func:`analyze_text_sync`，再在本地计算情感突变与情感转移，
    保留原有 ``sequence_analysis`` / ``sentiment_changes`` /
    ``emotion_transitions`` / ``overall_sentiment`` 输出结构。
    """
    if not texts:
        return {
            "sequence_analysis": [],
            "overall_sentiment": {"label": "neutral", "score": 0.5},
            "sentiment_changes": [],
            "emotion_transitions": [],
            "analysis_count": 0,
        }

    sequence_analysis: list[dict[str, Any]] = []
    previous_score: float | None = None
    previous_emotion: str | None = None
    sentiment_changes: list[dict[str, Any]] = []
    emotion_transitions: list[dict[str, Any]] = []

    for i, text in enumerate(texts):
        try:
            result = analyze_text_sync(str(text), mode)
        except Exception as exc:  # noqa: BLE001 - 序列分析需要容错
            logger.warning("序列第 %d 条分析失败，回退中性: %s", i, exc)
            result = {
                "score": 0.5,
                "label": "neutral",
                "emotion": "无感",
                "source": "fallback",
                "error": True,
            }

        sequence_analysis.append({"index": i, "text": text, "sentiment": result})

        current_score = float(result.get("score", 0.5))
        current_emotion = result.get("emotion")

        if previous_score is not None:
            score_diff = abs(current_score - previous_score)
            if score_diff > 0.3:
                sentiment_changes.append(
                    {
                        "from_index": i - 1,
                        "to_index": i,
                        "from_score": previous_score,
                        "to_score": current_score,
                        "change_score": score_diff,
                        "from_label": sequence_analysis[i - 1]["sentiment"].get(
                            "label"
                        ),
                        "to_label": result.get("label"),
                    }
                )

        if previous_emotion is not None and current_emotion != previous_emotion:
            emotion_transitions.append(
                {
                    "from_index": i - 1,
                    "to_index": i,
                    "from_emotion": previous_emotion,
                    "to_emotion": current_emotion,
                }
            )

        previous_score = current_score
        previous_emotion = current_emotion

    scores = [float(item["sentiment"].get("score", 0.5)) for item in sequence_analysis]
    average_score = sum(scores) / len(scores) if scores else 0.5
    if average_score >= 0.6:
        overall_label = "positive"
    elif average_score <= 0.4:
        overall_label = "negative"
    else:
        overall_label = "neutral"

    return {
        "sequence_analysis": sequence_analysis,
        "overall_sentiment": {"label": overall_label, "score": average_score},
        "sentiment_changes": sentiment_changes,
        "emotion_transitions": emotion_transitions,
        "analysis_count": len(sequence_analysis),
    }


# ---------------------------------------------------------------------------
# Celery 任务定义
# ---------------------------------------------------------------------------


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
    """转发到主后端 ``/api/model/retrain``。

    主后端会再投递到自己的 Celery 队列，这里只负责拿到 task_id 并回报。
    """
    task_id = self.request.id
    self.update_state(
        state="PROGRESS",
        meta={"current": 1, "total": 2, "status": "正在转发重训练请求..."},
    )
    data = _post("/api/model/retrain", {"optimize": bool(optimize)})
    return {
        "status": "success",
        "task_id": task_id,
        "backend_task_id": data.get("task_id"),
        "optimized": bool(optimize),
        "note": "已转发至主后端 /api/model/retrain",
    }


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def analyze_sequence_task(self, texts: list[str], mode: str = "custom") -> dict[str, Any]:
    task_id = self.request.id
    self.update_state(
        state="PROGRESS",
        meta={"current": 0, "total": len(texts), "status": "正在执行序列情感分析..."},
    )
    result = analyze_sequence_sync(texts=texts, mode=mode)
    return {"status": "success", "task_id": task_id, "mode": mode, "result": result}
