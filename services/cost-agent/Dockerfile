FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY services/cost-agent/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared utilities and service source
COPY shared ./shared
COPY services/cost-agent/src/ ./src/
COPY services/cost-agent/pyproject.toml ./pyproject.toml

# Ensure shared package is importable
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8001/api/v1/live', timeout=5).raise_for_status()" || exit 1

# Run FastAPI with uvicorn
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
