# repo-root/app/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps required for sqlite and building wheels (kept minimal)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    libsqlite3-dev \
    sqlite3 \
 && rm -rf /var/lib/apt/lists/*

# copy application code
COPY . /app

# pip install requirements
RUN pip install --upgrade pip
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# create data dir (will be mounted by Ansible)
RUN mkdir -p /app/data && chown -R 1000:1000 /app/data

# create app user to run as non-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

ENV SQLITE_DB_PATH=/app/data/demoDB.sqlite
ENV FLASK_ENV=production
ENV FLASK_APP=backend/main.py

USER appuser

# prefer gunicorn if installed; fallback to direct run
CMD ["sh", "-c", "if command -v gunicorn >/dev/null 2>&1; then exec gunicorn -b 0.0.0.0:80 backend.main:app; else exec python3 backend/main.py; fi"]

