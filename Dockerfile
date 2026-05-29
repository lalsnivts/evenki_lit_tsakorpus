# ---- Evenki Tsakorpus ----
# Multi-stage build:
#   1) indexer – downloads data, converts, and indexes into Elasticsearch
#   2) web     – runs the Flask search interface (default)

# ============================================================
# Stage: base – shared Python environment
# ============================================================
FROM python:3.12-slim AS base

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
# 'datasets' is needed only for the HF data-download step,
# but we install it in base so both stages share the layer.
RUN pip install --no-cache-dir -r requirements.txt datasets

COPY . .
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]

# ============================================================
# Stage: indexer – one-shot container that populates ES
# Run:  docker compose --profile indexing run --rm indexer
# ============================================================
FROM base AS indexer

CMD ["sh", "-c", "\
    echo '==> Waiting for Elasticsearch...' && \
    until curl -sf http://${ELASTICSEARCH_HOST:-localhost}:9200/_cluster/health >/dev/null 2>&1; do sleep 2; done && \
    echo '==> Elasticsearch is ready.' && \
    echo '==> Downloading dataset from HuggingFace...' && \
    cd /app/data_raw && python get_meta_data.py && \
    echo '==> Converting to tsakorpus JSON...' && \
    cd /app/src_convertors && python hf2json.py && \
    echo '==> Indexing into Elasticsearch...' && \
    cd /app/indexator && python indexator.py && \
    echo '==> Done! Corpus indexed successfully.' \
"]

# ============================================================
# Stage: web – the Flask search UI (default)
# ============================================================
FROM base AS web

EXPOSE 7342

WORKDIR /app/search

CMD ["python", "tsakorpus.wsgi"]
