#!/usr/bin/env bash

set -e

migrations() {
  echo "Apply database migrations..."
  poetry run python manage.py migrate --skip-checks --no-input
}

django_checks() {
  echo "Running Django checks"
  poetry run python manage.py check
}

startup() {
  migrations

  django_checks

  poetry run gunicorn project_lynx.wsgi:application --bind 0.0.0.0:8000 
}

startup
