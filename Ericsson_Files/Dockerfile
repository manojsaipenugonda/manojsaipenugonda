FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (matches existing K8s Service)
EXPOSE 8002

# Force unbuffered stdout/stderr so logs appear in kubectl logs immediately
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run via the app's entry point (reads API_PORT from env, defaults to 8000)
# Override with --port to match the K8s Service on 8002
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1", "--timeout-keep-alive", "120", "--log-level", "info"]
