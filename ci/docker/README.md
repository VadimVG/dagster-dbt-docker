# Docker Compose

This guide shows how to run the dagster-dbt project locally with Docker Compose.

- All services run as containers of one Compose project, `dagster-dbt`.
- Passwords are read from the `.env` file next to the Compose file.
- The data warehouse (DWH) runs **outside** this project, as a separate Docker Compose project.

Run all commands from the `ci/docker` folder.

## 1. What runs in Compose

- **Dagster webserver** – the main UI, where you see and run jobs.
- **Dagster daemon** – runs schedules and picks up queued runs in the background.
- **Dagster user code server** – loads your custom Dagster code (jobs, assets, resources) and serves it over gRPC.
- **PostgreSQL (Dagster)** – stores Dagster's run history, schedules, and event logs.
- **Celery executor** – runs the actual steps of a job, through RabbitMQ and Redis.
- **dbt docs service** – prepares the dbt project files and serves the dbt documentation site.
- **RabbitMQ** – message broker between Dagster and the Celery executor.
- **Redis** – stores the results of Celery tasks.
- **Flower** – web UI for watching Celery tasks.

All containers use the Docker network `data-platform-net`. The DWH project creates this network, so the containers can reach the DWH by name.


## 2. The .env file

The `.env` file must be next to the Compose file. Do not commit real passwords. `.env` is in `.gitignore`, but a file that git already tracks stays tracked. Remove it from the index once with `git rm --cached ci/docker/.env`.

```bash
# ===== Data Warehouse (dbt) =====
DWH_USER=""
DWH_PASSWORD=""
DWH_PORT=""
DWH_DB=""
DWH_HOST=""

# ===== Dagster PostgreSQL =====
PG_USERNAME=dagster_user
PG_PASSWORD=dagster_password
PG_HOST=dagster-postgresql
PG_PORT=5432
PG_DB=dagster

# ===== RabbitMQ =====
DEFAULT_VHOST=/
DEFAULT_USER=guest
DEFAULT_PASS=guest

# ===== Celery =====
CELERY_BROKER_URL=pyamqp://guest:guest@dagster-rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://dagster-redis:6379/0
```

Keep `PG_PORT=5432`. Postgres listens on 5432 inside the container, the Compose file publishes `${PG_PORT}:${PG_PORT}`, and `app/dagster_home/dagster.yaml` has the port `5432` written in it. Another value breaks the port mapping, or you must change both files.

The user and password in `CELERY_BROKER_URL` must be the same as `DEFAULT_USER` and `DEFAULT_PASS`. The host names (`dagster-rabbitmq`, `dagster-redis`) are the Compose container names.

Dagster reads its instance config from `app/dagster_home/dagster.yaml` and `app/dagster_home/workspace.yaml`. The Kubernetes chart has its own copies in `ci/k8s/dagster-dbt-chart/files/`. Keep both copies in sync. After you change these files, run `docker compose restart`.

## 3. Start

```bash
docker compose up -d --build
docker compose ps
```

Web interfaces:

- Dagster: http://localhost:3000
- dbt docs: http://localhost:8001
- Flower: http://localhost:5555
- RabbitMQ: http://localhost:15672

## 4. Daily work

The code is mounted from `../../app/` (the code is two folders up), so you do not need to build the image after code changes.

After a change in the Python code:

```bash
docker compose restart dagster-user-code dagster-celery-executor
```

After a change in the dbt models (to build `manifest.json` again):

```bash
docker compose restart dbt-docs-and-prepare-project
```

Build the images again only when the Dockerfiles or `requirements.txt` change:

```bash
docker compose up -d --build
```

Logs:

```bash
docker compose logs -f dagster-daemon
```

To check that the paths in the Compose file are correct without starting anything:

```bash
docker compose config | grep "source:"
```

All paths must point to the `app` folder in the repository root.

## 5. Stop

```bash
docker compose down
```


## 6. How it works
 
The flow in simple words:

1. You trigger a job in the Dagster webserver, or a schedule starts it. The run goes into the queue.
2. The daemon takes the run from the queue and launches it through the user code server.
3. The run process (in the user code container) sends each step to Celery through RabbitMQ.
4. A Celery worker (the executor) picks up the step and runs it — usually a dbt command.
5. dbt transforms the raw data in the Analytics PostgreSQL database.
6. Redis stores the Celery task results. Dagster writes the run events to its own Postgres. You can watch progress in the Dagster UI and in Flower.

### Celery executor in detail
 
![celery_executor](/readme_images/celery_executor.png)

