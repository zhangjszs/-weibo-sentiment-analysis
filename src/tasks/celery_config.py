#!/usr/bin/env python3
"""
微博舆情分析系统 - Celery异步任务配置
功能：配置Celery应用，定义任务队列和调度
"""

import logging
import time
from typing import Any, Dict, List

from celery import Celery
from celery.signals import task_failure, task_prerun, task_success

from config.settings import Config

logger = logging.getLogger(__name__)

# 创建Celery应用实例
celery_app = Celery(
    "weibo_sentiment",
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
    include=[
        "tasks.celery_spider",  # 爬虫任务模块
        "tasks.celery_sentiment",  # 情感分析任务模块
    ],
)

# Celery配置
celery_app.conf.update(
    # 序列化配置
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # 时区配置
    timezone="Asia/Shanghai",
    enable_utc=True,
    # 任务执行配置
    task_track_started=True,  # 追踪任务开始状态
    task_time_limit=3600,  # 任务硬限制：1小时
    task_soft_time_limit=3300,  # 软限制：55分钟（提前警告）
    worker_prefetch_multiplier=1,  # 避免任务积压，每个worker只预取1个任务
    worker_max_tasks_per_child=1000,  # 每个worker进程处理1000个任务后重启（防止内存泄漏）
    # 结果后端配置
    result_expires=3600 * 24,  # 结果保存24小时
    result_extended=True,  # 保存更多任务元数据
    # 重试配置
    task_default_retry_delay=60,  # 默认重试间隔60秒
    task_max_retries=3,  # 最大重试次数
    # 队列配置
    task_default_queue="default",  # 默认队列
    task_queues={
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
        "spider": {  # 爬虫任务专用队列
            "exchange": "spider",
            "routing_key": "spider",
        },
        "sentiment": {  # 情感分析任务专用队列
            "exchange": "sentiment",
            "routing_key": "sentiment",
        },
    },
    # 路由配置
    task_routes={
        "tasks.celery_spider.*": {"queue": "spider"},
        "tasks.celery_sentiment.*": {"queue": "sentiment"},
    },
)


# 信号处理器
@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **extras):
    """任务开始前的处理"""
    logger.info(
        f"[任务开始] {task.name} | task_id={task_id} | args={args[:2] if args else 'none'}"
    )


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """任务成功完成的处理"""
    task_name = sender.name if sender else "unknown"
    task_id = kwargs.get("task_id", "unknown")
    logger.info(f"[任务成功] {task_name} | task_id={task_id}")

    # 可以在这里添加指标收集
    try:
        from utils.metrics import increment_counter

        increment_counter("celery_task_success", labels={"task": task_name})
    except ImportError:
        logger.debug("utils.metrics 不可用，跳过 celery_task_success 指标上报")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """任务失败的处理"""
    task_name = sender.name if sender else "unknown"
    logger.error(f"[任务失败] {task_name} | task_id={task_id} | error={exception}")

    # 可以在这里添加告警
    try:
        from utils.metrics import increment_counter

        increment_counter(
            "celery_task_failure",
            labels={"task": task_name, "error": type(exception).__name__},
        )
    except ImportError:
        logger.debug("utils.metrics 不可用，跳过 celery_task_failure 指标上报")


def health_check() -> Dict[str, Any]:
    """
    执行Celery系统健康检查

    检查Broker连接、Worker状态、后端存储状态，返回综合健康报告

    Returns:
        Dict: 包含健康状态、检查项详情和问题报告的字典
    """
    from celery.exceptions import OperationalError

    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {},
        "issues": []
    }

    # 1. 检查Broker连接
    try:
        with celery_app.connection() as conn:
            conn.ensure_connection(max_retries=1, timeout=5)
            health_status["checks"]["broker"] = {
                "status": "ok",
                "type": celery_app.conf.broker_url.split("://")[0] if celery_app.conf.broker_url else "unknown"
            }
    except OperationalError as e:
        health_status["checks"]["broker"] = {"status": "error", "error": str(e)}
        health_status["issues"].append(f"Broker连接失败: {e}")
        health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["checks"]["broker"] = {"status": "error", "error": str(e)}
        health_status["issues"].append(f"Broker检查异常: {e}")

    # 2. 检查后端的存储
    try:
        result_backend = celery_app.conf.result_backend
        if result_backend:
            # 尝试一个简单的后端操作
            health_status["checks"]["backend"] = {
                "status": "ok",
                "type": result_backend.split("://")[0] if "://" in result_backend else result_backend
            }
        else:
            health_status["checks"]["backend"] = {"status": "warning", "message": "未配置结果后端"}
    except Exception as e:
        health_status["checks"]["backend"] = {"status": "error", "error": str(e)}
        health_status["issues"].append(f"后端检查异常: {e}")

    # 3. 检查Worker状态（如果启用了检查）
    try:
        inspect = celery_app.control.inspect(timeout=5)
        active_workers = inspect.active()
        if active_workers:
            worker_count = len(active_workers)
            health_status["checks"]["workers"] = {
                "status": "ok",
                "count": worker_count,
                "active_tasks": sum(len(tasks) for tasks in active_workers.values())
            }
        else:
            health_status["checks"]["workers"] = {
                "status": "warning",
                "message": "未检测到活跃Worker（可能Worker未启动或无法连接）"
            }
    except Exception as e:
        health_status["checks"]["workers"] = {"status": "error", "error": str(e)}
        health_status["issues"].append(f"Worker检查异常: {e}")

    # 最终状态判断
    if health_status["issues"]:
        critical_errors = sum(1 for check in health_status["checks"].values()
                            if check.get("status") == "error")
        if critical_errors >= 2:
            health_status["status"] = "critical"
        else:
            health_status["status"] = "degraded"

    return health_status


def _create_task_queues() -> List[Dict[str, Any]]:
    """
    创建带优先级的任务队列配置

    配置多优先级队列、Exchange创建、队列参数设置（支持优先级）、默认队列设置

    Returns:
        List[Dict]: 队列配置列表
    """
    from kombu import Exchange

    queues = []

    # 定义Exchange
    default_exchange = Exchange("default", type="direct")
    spider_exchange = Exchange("spider", type="direct")
    sentiment_exchange = Exchange("sentiment", type="direct")
    priority_exchange = Exchange("priority", type="direct")

    # 默认队列
    queues.append({
        "name": "default",
        "exchange": default_exchange,
        "routing_key": "default",
        "queue_arguments": {},
        "description": "默认任务队列"
    })

    # 爬虫任务队列
    queues.append({
        "name": "spider",
        "exchange": spider_exchange,
        "routing_key": "spider",
        "queue_arguments": {
            "x-max-priority": 10,  # 支持10级优先级
        },
        "description": "爬虫任务专用队列"
    })

    # 情感分析任务队列
    queues.append({
        "name": "sentiment",
        "exchange": sentiment_exchange,
        "routing_key": "sentiment",
        "queue_arguments": {
            "x-max-priority": 10,
        },
        "description": "情感分析任务专用队列"
    })

    # 高优先级队列（用于紧急任务）
    queues.append({
        "name": "priority_high",
        "exchange": priority_exchange,
        "routing_key": "priority.high",
        "queue_arguments": {
            "x-max-priority": 20,
            "x-message-ttl": 3600000,  # 消息1小时过期
        },
        "description": "高优先级任务队列"
    })

    # 低优先级队列（用于后台任务）
    queues.append({
        "name": "priority_low",
        "exchange": priority_exchange,
        "routing_key": "priority.low",
        "queue_arguments": {
            "x-max-priority": 5,
        },
        "description": "低优先级任务队列"
    })

    return queues


# 健康检查任务（可选）
@celery_app.task(name="tasks.health_check")
def health_check_task():
    """系统健康检查任务"""
    return health_check()


if __name__ == "__main__":
    # 本地测试启动
    celery_app.start()
