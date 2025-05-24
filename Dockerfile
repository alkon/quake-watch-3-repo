# Define Python version arguments
ARG PYTHON_VER=3.13
ARG PYTHON_SUB_VER=2

# Use the Python version argument to select the base image
FROM python:${PYTHON_VER}.${PYTHON_SUB_VER}-alpine AS builder

WORKDIR /app

RUN apk update && \
    apk add --no-cache \
    python3 \
    py3-pip && \
    # Remove cache to reduce size
    rm -rf /var/cache/apk/*

COPY requirements.txt .

# Install dependencies without caching
RUN pip install --no-cache-dir -r requirements.txt

# Final stage to reduce image size
FROM python:${PYTHON_VER}.${PYTHON_SUB_VER}-alpine AS final
WORKDIR /app
ARG PYTHON_VER

# Install curl in the final stage (for healthcheck from inside the container)
RUN apk update && \
    apk add --no-cache curl

# Copy the installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python${PYTHON_VER}/site-packages /usr/local/lib/python${PYTHON_VER}/site-packages

# Copy application files
COPY app.py .
COPY dashboard.py .
COPY utils.py .
COPY templates/ templates/

EXPOSE 5000

CMD ["python", "app.py"]
