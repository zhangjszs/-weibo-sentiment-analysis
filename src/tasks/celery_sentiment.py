#!/usr/bin/env python3
"""
情感分析异步任务模块
功能：批量情感分析、LLM降级缓存
"""

import hashlib
import json
import logging
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from config.settings import Config
from tasks.celery_config import celery_app

logger = logging.getLogger(__name__)

# 尝试导入Redis（可选依赖）
try:
    import redis

    redis_client = redis.Redis(**Config.get_redis_connection_params())
    REDIS_AVAILABLE = True
except Exception as e:
    logger.warning(f"Redis连接失败: {e}")
    redis_client = None
    REDIS_AVAILABLE = False


def get_cache_key(text: str, mode: str = "smart") -> str:
    """生成缓存键"""
    key_data = f"sentiment:{mode}:{text}"
    return hashlib.md5(key_data.encode()).hexdigest()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def analyze_sentiment_batch(
    self, texts: List[str], mode: str = "smart"
) -> Dict[str, Any]:
    """
    批量情感分析任务

    Args:
        texts: 待分析文本列表
        mode: 分析模式 (simple/smart/custom)

    Returns:
        dict: 批量分析结果
    """
    task_id = self.request.id
    logger.info(f"[任务{task_id}] 批量情感分析: {len(texts)}条文本, mode={mode}")

    results = []
    cached_count = 0
    llm_count = 0

    try:
        from services.sentiment_service import SentimentService

        for i, text in enumerate(texts):
            # 更新进度
            if i % 10 == 0:  # 每10条更新一次
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i,
                        "total": len(texts),
                        "status": f"已处理 {i}/{len(texts)} 条",
                    },
                )

            # 尝试从缓存获取
            if REDIS_AVAILABLE and mode == "smart":
                cache_key = get_cache_key(text, mode)
                cached = redis_client.get(cache_key)
                if cached:
                    result = json.loads(cached)
                    result["cached"] = True
                    results.append(result)
                    cached_count += 1
                    continue

            # 调用分析服务
            result = SentimentService.analyze(text, mode)
            result["cached"] = False
            results.append(result)

            if mode == "smart":
                llm_count += 1
                # 写入缓存
                if REDIS_AVAILABLE:
                    cache_key = get_cache_key(text, mode)
                    redis_client.setex(
                        cache_key, Config.LLM_CACHE_TTL, json.dumps(result)
                    )

        return {
            "status": "success",
            "task_id": task_id,
            "total": len(texts),
            "cached": cached_count,
            "llm_calls": llm_count,
            "results": results,
        }

    except Exception as exc:
        logger.error(f"[任务{task_id}] 批量分析失败: {exc}")
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_single_with_fallback(
    self, text: str, mode: str = "smart"
) -> Dict[str, Any]:
    """
    单条文本分析（带降级缓存）

    Args:
        text: 待分析文本
        mode: 分析模式

    Returns:
        dict: 分析结果，包含是否降级信息
    """
    task_id = self.request.id

    try:
        # 检查缓存
        if REDIS_AVAILABLE and mode == "smart":
            cache_key = get_cache_key(text, mode)
            cached = redis_client.get(cache_key)
            if cached:
                result = json.loads(cached)
                result["source"] = "cache"
                return result

        # 执行分析
        from services.sentiment_service import SentimentService

        result = SentimentService.analyze(text, mode)
        result["source"] = "llm" if mode == "smart" else "local"

        # 缓存结果
        if REDIS_AVAILABLE and mode == "smart":
            cache_key = get_cache_key(text, mode)
            redis_client.setex(cache_key, Config.LLM_CACHE_TTL, json.dumps(result))

        return result

    except Exception as exc:
        logger.error(f"[任务{task_id}] 分析失败，降级到SnowNLP: {exc}")

        # 降级到simple模式
        try:
            from services.sentiment_service import SentimentService

            result = SentimentService.analyze(text, "simple")
            result["source"] = "fallback"
            result["fallback_reason"] = str(exc)
            return result
        except Exception as e:
            logger.error(f"[任务{task_id}] 降级也失败: {e}")
            raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=1, default_retry_delay=300)
def retrain_model_task(self, optimize: bool = False) -> Dict[str, Any]:
    """
    模型重训练任务

    Args:
        optimize: 是否进行超参数优化

    Returns:
        dict: 训练结果
    """
    task_id = self.request.id
    logger.info(f"[任务{task_id}] 开始模型重训练, optimize={optimize}")

    try:
        self.update_state(
            state="PROGRESS", meta={"status": "正在准备训练数据...", "progress": 10}
        )

        import sys
        from pathlib import Path

        model_dir = Path(Config.BASE_DIR) / "model"
        sys.path.insert(0, str(model_dir))

        self.update_state(
            state="PROGRESS", meta={"status": "正在训练模型...", "progress": 30}
        )

        if optimize:
            from pathlib import Path

            from model.trainModel import evaluate_models, load_data, train_best_model

            df = load_data(Path(model_dir) / "target.csv")
            results = evaluate_models(df, scoring="macro_f1")

            mean_scores = {name: scores.mean() for name, scores in results.items()}
            best_model_name = max(mean_scores, key=mean_scores.get)

            self.update_state(
                state="PROGRESS",
                meta={
                    "status": f"正在保存最优模型 ({best_model_name})...",
                    "progress": 80,
                },
            )

            train_best_model(df, model_name=best_model_name)

            return {
                "status": "success",
                "task_id": task_id,
                "best_model": best_model_name,
                "score": mean_scores[best_model_name],
                "optimized": True,
            }
        else:
            from pathlib import Path

            from model.trainModel import load_data, train_best_model

            df = load_data(Path(model_dir) / "target.csv")
            train_best_model(df, model_name="NaiveBayes")

            return {
                "status": "success",
                "task_id": task_id,
                "best_model": "NaiveBayes",
                "optimized": False,
            }

    except Exception as exc:
        logger.error(f"[任务{task_id}] 模型重训练失败: {exc}")
        self.update_state(
            state="FAILURE", meta={"status": f"训练失败: {str(exc)}", "error": str(exc)}
        )
        raise
