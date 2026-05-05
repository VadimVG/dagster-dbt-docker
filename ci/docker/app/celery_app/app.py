from celery import Celery
from dagster_celery.tasks import create_task
from kombu import Queue
import os

app = Celery('dagster')

app.conf.update(
    broker_url=os.environ.get('CELERY_BROKER_URL'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND'),
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_always_eager=False,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue='dagster',
    task_queues=(
        Queue('dagster', queue_arguments={'x-max-priority': 10}),
    ),
    task_queue_max_priority=10,
    task_default_priority=5,
)

execute_plan = create_task(app)

if __name__ == '__main__':
    app.worker_main()