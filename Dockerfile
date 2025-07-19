FROM python:3.13-slim-bookworm AS builder

# Install uv
RUN pip install uv

WORKDIR /app

# Copy project files
COPY ["pyproject.toml", "README.md", "./"]
COPY README.md .
COPY src/ ./src/

# Create a virtual environment and install dependencies
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install the package
RUN uv pip install .

# Runtime stage
FROM python:3.13-slim-bookworm

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set up environment
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# Copy application files
COPY src/ ./src/
COPY jenkins_github_app_auth.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "jenkins_github_app_auth.py"]
