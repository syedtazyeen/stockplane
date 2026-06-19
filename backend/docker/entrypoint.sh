#!/bin/sh
set -e

if [ -n "${DATABASE_URL:-}" ] && [ "${SKIP_MIGRATIONS:-}" != "true" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

exec "$@"
