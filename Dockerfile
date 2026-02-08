# GLM-OCR RunPod Serverless Worker using vLLM OpenAI server
FROM vllm/vllm-openai:nightly

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (should already be present, but keep minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install only what we need on top of vLLM image
COPY requirements-runpod.txt ./
RUN pip install --no-cache-dir -r requirements-runpod.txt \
    && find /usr/local/lib -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib -name "*.pyc" -delete 2>/dev/null || true \
    && rm -rf /root/.cache /tmp/* 2>/dev/null || true

COPY handler.py ./

# Use system Python so we run handler.py; image's "python" may be a vllm CLI wrapper
CMD ["/usr/bin/python3", "-u", "handler.py"]
