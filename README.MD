# 🧩➡️🏭➡️🚛 ETL Pipeline with Dagster & dbt

**Description**: This project implements an ETL process using Dagster (orchestration) and dbt (data transformation).

![diagram.png](/readme_images/diagram.png)

## 🛠️ Technologies
- **Dagster** – pipeline orchestration (https://dagster.io/)
- **dbt (data build tool)** – data transformation (https://www.getdbt.com/)
- **PostgreSQL (Dagster)** - database for dagster launches, schedules, and event logs.
- **RabbitMQ** - message broker for dagster
- **Redis** - backend results for dagster
- **Celery** - distributed task queue for dagster
- **Flower** - celery monitoring
- **PostgreSQL (Analytics)** - database for analytics
- **Docker** - containerization
- **Python libs for data manipulation**


## ⚙️ Installation

### Preliminary requirements
- Python 3.11+
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

### 3. Create database for analytics (you can use default .env for testing)
```bash
cd ci\docker\analytics_db
docker-compose up -d
```

### 4. Create dagster-dbt project (you can use default .env for testing)
```bash
cd ci\docker
docker-compose up -d
```

## 🚀 Launch and testing

### 1. Go to the http://localhost:3000/overview/activity/timeline
You should see the following:
![start_page.png](/readme_images/start_page.png)


### 2. Run test jobs to check the project's functionality
**Open the sidebar.**
- **choose verify_database_availability_job -> click "materialize"**
- **choose example_1_job -> click "materialize all"**
- **choose example_2_job -> click "launchpad" -> click "launch run"**
- **choose example_3_job -> click "launchpad" -> click "launch run"**

### ***if all jobs was successfully this project ready to work.***

# **Enjoy the beautiful dagster and dbt 🎉✨**


## ℹ️ Useful info

### Monitoring
| Service | Port | URL |
|---------|------|-----|
| Dagster UI | 3000 | http://localhost:3000 |
| dbt docs | 8001 | http://localhost:8001 |
| Flower | 5555 | http://localhost:5555 |
| RabbitMQ UI | 15672 | http://localhost:15672 |

### How Celery Executor works
![start_page.png](/readme_images/celery_executor.png)




