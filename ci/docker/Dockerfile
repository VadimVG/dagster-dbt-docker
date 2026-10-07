FROM python:3.11


ENV DAGSTER_HOME=/opt/dagster/app/dagster_home/

WORKDIR /tmp
COPY requirements.txt .

RUN pip3 install --no-cache-dir -r /tmp/requirements.txt 

RUN mkdir -p $DAGSTER_HOME /opt/dagster/app

WORKDIR /opt/dagster/app


