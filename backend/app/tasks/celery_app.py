from celery import Celery
from app.core.config import settings

celery_app = Celery("imcs", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_BROKER_URL,
    include=["app.tasks.kb_tasks", "app.tasks.report_tasks"])
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"],
    timezone="Asia/Shanghai", task_acks_late=True, worker_prefetch_multiplier=1, task_soft_time_limit=300)
