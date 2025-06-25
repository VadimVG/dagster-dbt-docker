# 🧩➡️🏭➡️🚛 ETL Pipeline with Dagster & dbt

**Description**: This project implements an ETL process using Dagster (orchestration) and dbt (data transformation).

## How you can use this project
![schema.png](/readme_images/diagram.png)

## 🛠️ Technologies
- **Dagster** – pipeline orchestration (https://dagster.io/)
- **dbt (data build tool)** – data transformation (https://www.getdbt.com/)
- **PostgreSQL** - database for dagster launches, schedules, and event logs.
- **RabbitMQ** - message broker for dagster
- **KeyDB** - backend results for dagster
- **Celery** - distributed task queue for dagster
- **Flower** - celery monitoring
- **PostgreSQL** - analytics database
- **Docker** - containerization
- **Python libs for data manipulation**

## ⚙️ Installation

### Preliminary requirements
- Python 3.10+
- Docker
- Love of ETL ❤️

### 1. Clone repository
```bash
git clone https://github.com/VadimVG/dagster-dbt-docker.git
cd dagster-dbt-docker
```

### 2. Create docker network
```bash
docker network create dagster_dbt_network
```


### 3. Go to the ci\docker\analytics_db directory and create a .env file for the analytics_db and create database
```
DWH_USER=...
DWH_PASSWORD=...
DWH_HOST=...
DWH_PORT=...
DWH_DB=...
```

```bash
docker-compose up -d
```
### 4. Go to the ci\docker directory and create a .env file for the dagster-dbt project and create project
```
DWH_USER=...
DWH_PASSWORD=...
DWH_HOST=...
DWH_PORT=...
DWH_DB=...

PG_USERNAME=...
PG_PASSWORD=...
PG_HOST=...
PG_DB=...

DEFAULT_VHOST=/
DEFAULT_USER=...
DEFAULT_PASS=...   

CELERY_BROKER_URL=amqp://user:password@dagster-rabbitmq:<port>
CELERY_BROKER_URL_PY=pyamqp://user:password@dagster-rabbitmq:<port>
CELERY_RESULT_BACKEND=redis://dagster-keydb:<port>
CELERY_RESULT_BACKEND_=redis://dagster_keydb:<port>
```

```bash
docker-compose up -d
```


## 🚀 Launch and testing

### 1. Go to the http://localhost:3000/overview/activity/timeline
You should see the following:
![start_page.png](readme_images\start_page.png)


### 2. Run test jobs to check the project's functionality
**Open the sidebar.**
- **choose verify_database_availability_job -> click "materialize"**
- **choose example_1_job -> click "materialize all"**
- **choose example_2_job -> click "launchpad" -> click "launch run"**
- **choose example_3_job -> click "launchpad" -> click "launch run"**

### ***if all jobs was successfully this project ready to work.***


# **Enjoy the beautiful dagster and dbt 🎉✨**







