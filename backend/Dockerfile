FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck + postgresql-client for pg_isready
RUN apt-get update && apt-get install -y --no-install-recommends curl postgresql-client && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy alembic config
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Copy application
COPY app/ ./app/

# Copy entrypoint
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application via entrypoint (runs migrations first)
ENTRYPOINT ["./entrypoint.sh"]
