#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
if [ ! -f .env ]; then cp .env.example .env; fi
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createcachetable
.venv/bin/python manage.py import_locations --cities
if [ "${1:-}" = "--demo" ]; then
  .venv/bin/python manage.py import_fuel fixtures/public_demo_prices.csv
else
  mkdir -p data/raw
  if [ ! -f data/raw/fuel-prices-for-be-assessment.csv ] && [ -f fuel-prices-for-be-assessment.csv ]; then
    cp fuel-prices-for-be-assessment.csv data/raw/fuel-prices-for-be-assessment.csv
  fi
  .venv/bin/python manage.py import_fuel
fi
.venv/bin/python manage.py import_locations --verified data/reference/verified_stations.json
.venv/bin/python manage.py check
printf '%s\n' 'Ready. Run: .venv/bin/python manage.py runserver'
