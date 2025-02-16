# celery_app.py
from celery import Celery
from app.config import settings

celery = Celery(
    'agent_backend',
    broker=settings.redis_url,
    backend='rpc://'
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Import tasks so they are registered.
import app.tasks  # This ensures tasks in app/tasks.py are discovered.
