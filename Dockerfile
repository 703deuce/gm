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

# Install with the Python we will use at runtime (same interpreter = runpod on sys.path)
COPY requirements-runpod.txt ./
RUN /usr/bin/python3 -m ensurepip --default-pip 2>/dev/null || true \
    && /usr/bin/python3 -m pip install --no-cache-dir -r requirements-runpod.txt \
    && find /usr/local/lib /usr/lib -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib /usr/lib -name "*.pyc" -delete 2>/dev/null || true \
    && rm -rf /root/.cache /tmp/* 2>/dev/null || true

COPY handler.py ./

# Force rebuild: install and runtime use same interpreter
ENTRYPOINT ["/usr/bin/python3"]
CMD ["-u", "handler.py"]
