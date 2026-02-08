"""
Quick test script for the GLM-OCR RunPod serverless endpoint.
Sends glmocr-runpod/test.jpg to the endpoint and prints the OCR result.
"""
import os
import sys
import base64
import requests

# Credentials (override with env vars in production)
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "rpa_5B3UJFTJCQW65L0IZPHBOUC41742AESP9B378LSQrf9q5a")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID", "jsg755sv73y37a")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_IMAGE_PATH = os.path.join(SCRIPT_DIR, "test.jpg")
RUNSYNC_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"


def main():
    if not os.path.isfile(TEST_IMAGE_PATH):
        print(f"Error: Test image not found at {TEST_IMAGE_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(TEST_IMAGE_PATH, "rb") as f:
        raw = f.read()
    b64 = base64.standard_b64encode(raw).decode("ascii")
    image_url = f"data:image/jpeg;base64,{b64}"

    payload = {
        "input": {
            "prompt": "Text Recognition:",
            "image_url": image_url,
        }
    }

    # Wait up to 5 minutes (cold start + model load + OCR)
    url_with_wait = f"{RUNSYNC_URL}?wait=300000"
    # RunPod expects the API key as the Authorization header value (no "Bearer " prefix)
    headers = {
        "Authorization": RUNPOD_API_KEY,
        "Content-Type": "application/json",
    }

    print("Sending request to RunPod (this may take a while on cold start)...")
    resp = requests.post(url_with_wait, json=payload, headers=headers, timeout=310)

    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    status = data.get("status", "")
    if status != "COMPLETED":
        print(f"Job status: {status}")
        print(data)
        sys.exit(1)

    output = data.get("output", {})
    if "error" in output:
        print("Error from handler:", output["error"], file=sys.stderr)
        sys.exit(1)

    text = output.get("output", "")
    print("--- OCR result ---")
    print(text)
    print("---")
    if data.get("executionTime"):
        print(f"Execution time: {data['executionTime']} ms")


if __name__ == "__main__":
    main()
