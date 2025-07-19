# Dockerfile.multistage
# Build stage - Use Python 3.13 with uv installed
FROM python:3.13-slim-bookworm AS builder

# Install uv via pip (simpler and more reliable in Docker)
RUN pip install uv

WORKDIR /app

# Copy only the dependency files first
COPY pyproject.toml .

# Create a virtual environment and install dependencies
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies from pyproject.toml
RUN uv pip install .

# Runtime stage
FROM python:3.13-slim-bookworm

# Install runtime dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Copy the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set up environment
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# Copy application files
COPY github_app_auth.py .
COPY jenkins_github_app_auth.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "jenkins_github_app_auth.py"]