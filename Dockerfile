# Expert LLM System - Ultra-Optimized Docker Build
# Minimal image size with essential components only

# Stage 1: Minimal base with Python
FROM python:3.11-slim-bullseye as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install only essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Essential networking and SSL
    curl ca-certificates \
    # Minimal build tools for Python packages
    gcc g++ \
    # Process management
    supervisor \
    # Cleanup in same layer to reduce size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Ollama in optimized way
RUN curl -fsSL https://ollama.com/install.sh | sh && \
    rm -rf /tmp/* /var/tmp/*

# Stage 2: Python dependencies (optimized)
FROM base as dependencies

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy and install Python dependencies in one layer
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf ~/.cache/pip

# Stage 3: Final application (minimal)
FROM dependencies as application

# Copy only essential application files
COPY src/ ./src/
COPY setup.sh health_check.sh setup-ollama.sh ./
COPY docker/supervisord.conf /etc/supervisor/conf.d/
COPY docker/entrypoint.sh /entrypoint.sh

# Create directories and set permissions in single layer
RUN mkdir -p logs temp data/backups /usr/share/ollama/.ollama /etc/supervisor/conf.d && \
    chown -R appuser:appuser /app /usr/share/ollama && \
    chmod +x setup.sh health_check.sh setup-ollama.sh /entrypoint.sh && \
    # Remove unnecessary files to reduce size
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /root/.cache

# Expose only necessary port
EXPOSE 8501

# Minimal health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=2 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Set entrypoint and default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["streamlit"]

