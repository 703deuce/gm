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

# Install into the same interpreter we'll run; record its path for runtime
COPY requirements-runpod.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements-runpod.txt \
    && which python3 > /app/.python3_path \
    && find /usr/local/lib /usr/lib -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib /usr/lib -name "*.pyc" -delete 2>/dev/null || true \
    && rm -rf /root/.cache /tmp/* 2>/dev/null || true

COPY handler.py ./
COPY run_handler.sh /app/run_handler.sh
RUN chmod +x /app/run_handler.sh

# Run with the exact Python that received pip install (avoids PATH differences at runtime)
ENTRYPOINT ["/app/run_handler.sh"]
