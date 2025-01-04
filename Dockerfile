# Use Python 3.10.16 as base image
FROM python:3.10.16-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Production stage
FROM python:3.10.16-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBUG=False

# Install system dependencies and Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    cron \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m appuser && \
    mkdir -p /home/appuser/app && \
    chown -R appuser:appuser /home/appuser/app

# Set working directory
WORKDIR /home/appuser/app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from builder
COPY --from=builder --chown=appuser:appuser /app/ ./

# Debug: Show files and permissions
RUN ls -la && \
    echo "=== Script Permissions ===" && \
    ls -la start.sh healthcheck.sh

# Set permissions for scripts
RUN chmod +x start.sh healthcheck.sh

# Create the cron job file
RUN echo "*/15 * * * * cd /home/appuser/app && python manage.py runcrons >> /home/appuser/app/cron.log 2>&1" > /etc/cron.d/django-crons && \
    chmod 0644 /etc/cron.d/django-crons

# Create log file and set permissions
RUN touch cron.log && \
    chown appuser:appuser cron.log

# Create directory for cron locks
RUN mkdir -p cron_locks && \
    chown -R appuser:appuser cron_locks

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["./healthcheck.sh"]

# Start services
CMD ["./start.sh"] 