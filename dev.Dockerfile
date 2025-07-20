FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

RUN pip install uv

COPY ["pyproject.toml", "README.md", "./"]
COPY src/ ./src/

RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN uv pip install --editable ".[dev]"

FROM python:3.13-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY src/ ./src/
COPY jenkins_github_app_auth.py .
COPY README.md .
COPY pyproject.toml .

CMD ["bash"]