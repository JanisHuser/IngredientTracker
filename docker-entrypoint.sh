#!/bin/sh
set -e

# Initialize the database if it doesn't exist
flask db upgrade

# Calculate number of workers if not set
if [ -z "${WORKERS}" ]; then
    WORKERS=$(nproc)
fi

# Start Gunicorn
exec gunicorn --workers=$WORKERS \
    --bind 0.0.0.0:5000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    "app:app"