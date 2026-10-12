#!/usr/bin/env sh
set -eu
python -m pip install -r requirements.lock
python manage.py collectstatic --noinput
