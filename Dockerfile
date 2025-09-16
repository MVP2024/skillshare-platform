# Use official Python slim image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable stdout/stderr buffering
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies required to build some Python packages and to run the app
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       gcc \
       curl \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd -g 1000 app || true && useradd -m -u 1000 -g app app || true

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Ensure correct permissions for volumes
RUN chown -R app:app /app

USER app

# Expose the port that the app will run on
EXPOSE 8000

# Default command for production: run gunicorn
CMD ["gunicorn", "skillshare_platform.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-level", "info"]
