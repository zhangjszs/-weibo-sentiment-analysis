import os

from celery import Celery


def make_celery():
    return Celery(
        "nlp_worker",
        broker=os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
        backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
        include=["app.tasks"],
    )


celery_app = make_celery()

# Celery 5.x：启动时重试 broker 连接（docker-compose 启动顺序敏感需打开）
celery_app.conf.update(broker_connection_retry_on_startup=True)
