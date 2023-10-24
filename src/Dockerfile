FROM python:3.9-slim-bullseye

LABEL pipelineName="pnide-webapi"

USER root

RUN apt-get clean && apt-get update && apt-get install -y ffmpeg libsm6 libxext6 curl gnupg

RUN adduser --disabled-password --gecos '' pythonwebapi

WORKDIR /home/pythonwebapi
COPY requirements.txt requirements.txt
COPY logger_config.py logger_config.py

RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt && pip install gunicorn && pip install flake8

# ODBC 18 for SQL Server on Debian 11. If upgrading the O.S. or version, please consult the following link
# https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18

RUN apt-get remove -y ffmpeg curl gnupg

COPY app app
COPY init_app.py ./

ENV FLASK_APP init_app.py

RUN chown -R pythonwebapi:pythonwebapi ./
USER pythonwebapi

EXPOSE 8000 7000
ENTRYPOINT ["gunicorn","init_app:app","-k","uvicorn.workers.UvicornWorker","-b","0.0.0.0", "--timeout", "180"]
