#!/usr/bin/env sh
set -eu
# Direct connection for schema/seed work; pooled URL remains the app default.
if [ -n "${DATABASE_URL_UNPOOLED:-}" ]; then
  DATABASE_URL="$DATABASE_URL_UNPOOLED" python manage.py migrate --noinput
  DATABASE_URL="$DATABASE_URL_UNPOOLED" python manage.py createcachetable
  DATABASE_URL="$DATABASE_URL_UNPOOLED" python manage.py seed_demo
else
  python manage.py migrate --noinput
  python manage.py createcachetable
  python manage.py seed_demo
fi
exec gunicorn fuelroute.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 1 --threads 4 --timeout 90 --access-logfile - --error-logfile -
