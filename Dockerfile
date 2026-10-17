# syntax=docker/dockerfile:1

# ---- Etapa 1: instala dependências num venv isolado ----
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install -r /tmp/requirements.txt

# ---- Etapa 2: imagem final enxuta, sem ferramentas de build ----
FROM python:3.12-slim

ARG APP_VERSION=dev
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION}

RUN useradd --create-home --uid 10001 cafe

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY alembic.ini ./
COPY app ./app
COPY migrations ./migrations
COPY scripts ./scripts

USER cafe

EXPOSE 8000

# Forma shell: ${PORT:-8000} é resolvido em tempo de execução (o Render define PORT).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --start-interval=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT:-8000}/health', timeout=4)" || exit 1

CMD ["python", "-m", "scripts.start"]
