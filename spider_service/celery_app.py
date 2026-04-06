import os

from celery import Celery


def make_celery():
    celery = Celery(
        'spider_worker',
        broker=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
        backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
        include=['app.tasks']
    )

    return celery

celery_app = make_celery()
