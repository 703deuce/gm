# GLM-OCR RunPod Serverless Worker using Transformers (no vLLM)
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps + Python
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-pip \
        libglib2.0-0 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements-runpod.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements-runpod.txt \
    && find /usr/local/lib /usr/lib -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib /usr/lib -name "*.pyc" -delete 2>/dev/null || true \
    && rm -rf /root/.cache /tmp/* 2>/dev/null || true

COPY handler.py ./

ENTRYPOINT ["python3"]
CMD ["-u", "handler.py"]
