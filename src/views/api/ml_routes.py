"""情感分析、批量预测、策略监控与模型管理路由。

聚合 ``/api/sentiment/*``、``/api/predict/*``、``/api/model/*`` 三组 ML 相关端点。
"""

from flask import request

from config.settings import Config
from services.nlp_task_service import (
    analyze_batch,
    analyze_text,
    submit_analyze_task,
    submit_retrain_task,
)
from utils.api_response import error, ok
from utils.authz import admin_required
from utils.rate_limiter import rate_limit

from ._shared import bp, logger


# ---------------------------------------------------------------------------
# Route handlers – sentiment analysis
# ---------------------------------------------------------------------------


@bp.route("/sentiment/analyze", methods=["POST"])
@rate_limit(
    max_requests=30, window_seconds=60, error_message="情感分析请求过于频繁，请稍后再试"
)
def analyze_sentiment():
    """
    文本情感分析接口
    Body:
        text: 待分析文本
        mode: 分析模式 (simple/smart)，默认 simple
        async: 是否异步执行（默认false）
    """
    try:
        data = request.json
        text = data.get("text", "")
        mode = data.get("mode", "simple")
        is_async = data.get("async", False)

        if not text:
            return error("text is required", code=400), 400

        from utils.input_validator import validate_keyword

        validation = validate_keyword(text[:50])  # 只校验前50字符
        if not validation["valid"]:
            return error(validation["message"], code=400), 400

        if is_async:
            dispatch_result = submit_analyze_task(text=text, mode=mode)
            return ok(
                {
                    "task_id": dispatch_result["task_id"],
                    "status": dispatch_result.get("status", "PENDING"),
                    "check_url": f"/api/tasks/{dispatch_result['task_id']}/status",
                },
                msg="任务已提交",
                code=202,
            ), 202

        result = analyze_text(text=text, mode=mode)
        return ok(result), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("情感分析参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("情感分析服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("情感分析接口异常: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/predict/batch", methods=["POST"])
@rate_limit(
    max_requests=10, window_seconds=60, error_message="批量预测请求过于频繁，请稍后再试"
)
def predict_batch():
    """
    批量文本情感分析接口
    Body:
        texts: 待分析文本列表
        mode: 分析模式 (simple/smart/custom)，默认 custom
    """
    try:
        data = request.json
        texts = data.get("texts", [])
        mode = data.get("mode", "custom")

        if not texts or not isinstance(texts, list):
            return error("texts 必须是非空数组", code=400), 400

        if len(texts) > 100:
            return error("单次最多预测100条文本", code=400), 400

        results = analyze_batch(texts=texts, mode=mode)
        return ok({"total": len(results), "results": results}), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("批量预测参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("批量预测服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("批量预测接口异常: %s", e)
        return error("服务器内部错误", code=500), 500


# ---------------------------------------------------------------------------
# Route handlers – strategy monitoring
# ---------------------------------------------------------------------------


@bp.route("/sentiment/strategy/stats", methods=["GET"])
def get_strategy_stats():
    """获取情感分析策略性能统计"""
    try:
        from services.sentiment_strategy_selector import AdaptiveStrategyManager

        manager = AdaptiveStrategyManager()
        stats = manager.get_performance_stats()
        return ok(stats), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("获取策略统计参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("获取策略统计服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取策略统计失败: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/sentiment/strategy/health", methods=["GET"])
def get_strategy_health():
    """获取情感分析策略健康状态"""
    try:
        from services.sentiment_strategy_selector import AdaptiveStrategyManager

        manager = AdaptiveStrategyManager()
        health = manager.get_health_status()
        return ok(health), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("获取策略健康状态参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("获取策略健康状态服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取策略健康状态失败: %s", e)
        return error("服务器内部错误", code=500), 500


# ---------------------------------------------------------------------------
# Route handlers – model
# ---------------------------------------------------------------------------


@bp.route("/model/info", methods=["GET"])
def get_model_info():
    """获取模型信息接口"""
    try:
        import json
        import os
        from pathlib import Path

        model_dir = Path(Config.BASE_DIR) / "model"
        model_path = model_dir / "best_sentiment_model.pkl"

        info = {
            "model_type": "TF-IDF + 分类器",
            "best_model": "NaiveBayes",
            "accuracy": None,
            "f1_score": None,
            "training_samples": None,
            "last_updated": None,
            "model_exists": model_path.exists(),
        }

        if model_path.exists():
            from datetime import datetime

            mtime = os.path.getmtime(model_path)
            info["last_updated"] = datetime.fromtimestamp(mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        summary_path = model_dir / "analysis_summary.json"
        if summary_path.exists():
            try:
                with open(summary_path, encoding="utf-8") as f:
                    summary = json.load(f)
                    info["training_samples"] = summary.get("total_comments")
            except (ValueError, OSError) as e:
                logger.debug("读取训练摘要文件失败: %s", e)

        return ok(info), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("获取模型信息参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("获取模型信息服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取模型信息异常: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/model/retrain", methods=["POST"])
@admin_required
def retrain_model():
    """
    触发模型重训练（异步）
    Body:
        optimize: 是否进行超参数优化
    """
    try:
        data = request.json or {}
        optimize = data.get("optimize", False)

        dispatch_result = submit_retrain_task(optimize=bool(optimize))
        logger.info("模型重训练任务已提交: task_id=%s", dispatch_result["task_id"])

        return ok(
            {
                "task_id": dispatch_result["task_id"],
                "status": dispatch_result.get("status", "PENDING"),
                "check_url": f"/api/tasks/{dispatch_result['task_id']}/status",
            },
            msg="模型重训练任务已提交",
            code=202,
        ), 202
    except (ValueError, KeyError, TypeError) as e:
        logger.error("模型重训练参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("模型重训练服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("模型重训练接口异常: %s", e)
        return error("服务器内部错误", code=500), 500
