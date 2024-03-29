FROM python:3.11.4
ENV DEBIAN_FRONTEND=noninteractive \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.3.2 \
  PYSETUP_PATH="/opt/pysetup" \
  POETRY_HOME="/opt/pysetup/poetry" \
  POETRY_CACHE_DIR="/opt/pysetup/poetry_cache" \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

WORKDIR $PYSETUP_PATH

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
  && pip3 install poetry \

COPY poetry.lock pyproject.toml ./
  # Install poetry
RUN poetry install --no-root --only main \
    && rm -r ${POETRY_CACHE_DIR}/*

ENV VIRTUAL_ENV="${VENV_PATH}" \
    POETRY_VIRTUALENVS_CREATE=false


RUN poetry install  --with root,dev
