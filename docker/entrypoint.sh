#!/bin/sh
set -eu

sqlite_dir="$(dirname "${SQLITE_PATH:-/app/db.sqlite3}")"
mkdir -p "$sqlite_dir"

python manage.py migrate --noinput

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --worker-class gthread \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
