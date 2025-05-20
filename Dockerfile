FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt gunicorn

# Copy project files
COPY . .

# Create directories for data and static files
RUN mkdir -p /data
RUN mkdir -p /app/staticfiles
RUN mkdir -p /app/static
RUN mkdir -p /app/media

# Make scripts executable
RUN chmod +x build.sh
RUN chmod +x docker/wait-for-it.sh

# Create a non-root user to run the app
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app /data /app/staticfiles /app/static /app/media
USER appuser

# Run the build script (collects static files)
RUN ./build.sh build

# Command to run the application
CMD ["./build.sh", "django"] 