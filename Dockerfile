FROM python:3.11.4
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg2 dependencies
  libpq-dev \
  curl \
  git \
  gettext \
  # Install weasyprint dependencies
  python3-dev libblas-dev libatlas-base-dev gcc\
  # cleaning up unused files
  && apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/* \
  && pip3 install poetry
  # Install poetry

COPY poetry.lock pyproject.toml /usr/src/app/

RUN poetry install
