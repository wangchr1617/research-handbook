"""Celery 入口：celery -A demo.worker:celery_app worker -l INFO --concurrency=2。"""
from celery import Celery

from .config import settings
from .jobs import execute

celery_app = Celery("agent_demo", broker=settings().broker_url)
celery_app.conf.update(
    task_serializer="json", accept_content=["json"], result_serializer="json",
    task_ignore_result=True, task_acks_late=True, worker_prefetch_multiplier=1,
    task_soft_time_limit=25, task_time_limit=30,
    broker_transport_options={"visibility_timeout": 60, "socket_connect_timeout": 2, "socket_timeout": 2},
    broker_connection_timeout=2, task_publish_retry=False,
)


@celery_app.task(name="demo.execute")
def run_task(run_id):
    execute(run_id)


def enqueue(run_id):
    run_task.apply_async(args=[run_id], retry=False)
