#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for the database to be ready
# The wait-for-it.sh script is used to ensure the database container is up and running
# before the web service tries to connect to it.
./wait-for-it.sh database:5432 --timeout=30 --strict -- echo "Database is up"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the main process (gunicorn, uvicorn, etc.)
# "$@" allows us to pass arguments to the script, which will be executed as a command.
# For example, if the docker-compose command is `gunicorn ...`, "$@" will be `gunicorn ...`
exec "$@"
