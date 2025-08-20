# syntax=docker/dockerfile:1.7
# Base menor e atual: Debian Bookworm slim
FROM python:3.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Diretório de trabalho
WORKDIR /app

# 1) Depêndencias do SO (mudam pouco) -> ótima camada de cache
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr \
      tesseract-ocr-por \
      tesseract-ocr-eng \
      poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Usuário não-root e diretórios de trabalho
RUN useradd -u 1000 -m appuser \
 && mkdir -p /app/processed_pdfs \
 && chown -R appuser:appuser /app

# 2) Somente requirements primeiro (mantém cache das libs Python)
COPY requirements.txt /tmp/requirements.txt

# (Opcional, com BuildKit) cache de pip entre builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
 && pip install -r /tmp/requirements.txt

# Se não usar BuildKit, troque o bloco acima por:
# RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# 3) Agora sim, copie o restante do código (muda com frequência)
COPY --chown=1000:1000 . .

EXPOSE 8502

USER 1000:1000

CMD ["streamlit", "run", "main.py", "--server.port", "8502", "--server.address", "0.0.0.0"]
