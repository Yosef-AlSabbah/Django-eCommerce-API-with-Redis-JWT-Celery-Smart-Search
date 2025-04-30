# Pull official base Python Docker image
FROM python:3.12.3-slim

# Install system dependencies
# This layer is cached unless the base image or the list of packages changes
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
# These layers are cached as they don't depend on external files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
# This layer is cached unless the work directory path changes
WORKDIR /code

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies
# Copying `requirements.txt` first ensures this layer is cached if dependencies don't change
COPY requirements.txt .
RUN uv pip install --upgrade pip -r requirements.txt --system

# Copy the Django project
# This layer is rebuilt only if the project files change
COPY . .

# Expose the application port
# This layer is cached unless the exposed port changes
EXPOSE 8000

# Default command to run the application
# This layer is cached unless the command changes
CMD ["entrypoint.sh"]