# Use a minimal Python image
FROM python:3.12-slim as builder

# Prevent Python buffering
ENV PYTHONUNBUFFERED=1 \
    AWS_DEFAULT_REGION={{AWS_REGION}}

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Use a smaller runtime stage (multi-stage build optional)
FROM python:3.12-slim
WORKDIR /app

# Copy installed dependencies
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
# Copy code
COPY --from=builder /app /app

# Set entrypoint (use uvicorn if it's a FastAPI server)
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]