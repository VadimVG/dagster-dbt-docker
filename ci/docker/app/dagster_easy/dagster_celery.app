from celery import Celery
from dagster_celery.tasks import create_task

import os




app = Celery('dagster')

for k, v in os.environ.items():
    if k.startswith('CELERY_'):
        app.conf[k.lower()[7:]] = v

execute_plan = create_task(app)

if __name__ == '__main__':
    app.worker_main()