# handler.py
import os
import time
import threading
import subprocess
import requests
import runpod

VLLM_PORT = int(os.getenv("VLLM_PORT", "8080"))
VLLM_MODEL = os.getenv("VLLM_MODEL", "zai-org/GLM-OCR")
VLLM_BASE_URL = f"http://127.0.0.1:{VLLM_PORT}/v1"


def start_vllm_server():
    # Per GLM-OCR docs: vllm serve zai-org/GLM-OCR --allowed-local-media-path / --port 8080
    subprocess.Popen(
        [
            "vllm", "serve", VLLM_MODEL,
            "--allowed-local-media-path", "/",
            "--port", str(VLLM_PORT),
            "--host", "0.0.0.0",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


# Launch vLLM once on cold start
vllm_thread = threading.Thread(target=start_vllm_server, daemon=True)
vllm_thread.start()

# Wait for the server to come up
def wait_for_vllm(timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(VLLM_BASE_URL + "/models", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("vLLM server did not become ready in time")


wait_for_vllm()


def handler(event):
    """
    event["input"] should contain:
    - "prompt": base text prompt (e.g., "Text Recognition:")
    - "image_url": path or URL accessible from the container (e.g., /input/image.png)
    """
    inp = event.get("input", {}) or {}
    prompt = inp.get("prompt", "Text Recognition:")
    image_url = inp.get("image_url")

    if not image_url:
        return {"error": "image_url is required"}

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    payload = {
        "model": VLLM_MODEL,
        "messages": messages,
        "max_tokens": 8192,
    }

    resp = requests.post(
        VLLM_BASE_URL + "/chat/completions",
        json=payload,
        timeout=600,
    )
    resp.raise_for_status()
    data = resp.json()

    # Extract the text output
    content = data["choices"][0]["message"]["content"]
    return {"output": content}


runpod.serverless.start({"handler": handler})
