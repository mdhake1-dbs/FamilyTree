FROM python:3.11-slim

WORKDIR /app

# system deps (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
 && rm -rf /var/lib/apt/lists/*

# copy application code
COPY . /app

# install python deps if requirements.txt exists
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Create data dir (will be mounted by Ansible)
RUN mkdir -p /app/data && chown -R 1000:1000 /app/data

ENV SQLITE_DB_PATH=/app/data/demoDB.sqlite
ENV FLASK_APP=backend/main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=80

# ensure the app runs as non-root (optional)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Use gunicorn if available; fallback to flask run
CMD ["sh", "-c", "if command -v gunicorn >/dev/null 2>&1; then exec gunicorn -b 0.0.0.0:80 backend.main:app; else exec flask run --host=0.0.0.0 --port=80; fi"]

