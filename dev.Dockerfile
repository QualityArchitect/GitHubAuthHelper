FROM python:3.13-slim-bookworm

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Copy project configuration
COPY pyproject.toml .

# Install all dependencies including dev
RUN uv pip install --system -e ".[dev]"

# Set up for development
CMD ["bash"]