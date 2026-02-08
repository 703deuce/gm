#!/usr/bin/env python3
"""
Test the GLM-OCR RunPod serverless endpoint (this repo's handler).

Uses RunPod SDK so auth matches RunPod serverless. Our handler expects:
  input: { "prompt": "Text Recognition:", "image_url": "<url or data URI>" }
  output: { "output": "<OCR text>" }

Usage:
  # With env vars RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID:
  python test_endpoint.py
  python test_endpoint.py path/to/image.jpg

  # Or pass key and endpoint:
  python test_endpoint.py -e ENDPOINT_ID -k API_KEY
  python test_endpoint.py -e ENDPOINT_ID -k API_KEY ./image.png
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path

try:
    import runpod
except ImportError:
    print("Install runpod: pip install runpod", file=sys.stderr)
    sys.exit(1)

# Defaults (override with env or -e / -k)
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "rpa_5B3UJFTJCQW65L0IZPHBOUC41742AESP9B378LSQrf9q5a")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID", "jsg755sv73y37a")

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_IMAGE = SCRIPT_DIR / "test.jpg"


def image_to_data_uri(path: Path) -> str:
    raw = path.read_bytes()
    ext = path.suffix.lstrip(".").lower() or "png"
    mime = "png" if ext == "png" else "jpeg" if ext in ("jpg", "jpeg") else "png"
    b64 = base64.standard_b64encode(raw).decode("ascii")
    return f"data:image/{mime};base64,{b64}"


def main():
    parser = argparse.ArgumentParser(description="Test GLM-OCR RunPod serverless endpoint (this repo)")
    parser.add_argument(
        "image",
        nargs="?",
        default=str(DEFAULT_IMAGE),
        help="Path to image (default: test.jpg next to script)",
    )
    parser.add_argument("-e", "--endpoint-id", default=RUNPOD_ENDPOINT_ID, help="RunPod endpoint ID")
    parser.add_argument("-k", "--api-key", default=RUNPOD_API_KEY, help="RunPod API key")
    parser.add_argument("-t", "--timeout", type=int, default=300, help="Sync timeout in seconds")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print full response JSON")
    args = parser.parse_args()

    if not args.endpoint_id or not args.api_key:
        print("Set RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY, or use -e and -k.", file=sys.stderr)
        sys.exit(1)

    # Resolve image path
    p = Path(args.image).resolve()
    if not p.is_file():
        p2 = (SCRIPT_DIR / args.image).resolve()
        if p2.is_file():
            p = p2
        else:
            print(f"Image not found: {args.image}", file=sys.stderr)
            sys.exit(1)

    image_url = image_to_data_uri(p)

    # Our handler expects: input.prompt, input.image_url → output.output (text)
    job_input = {
        "prompt": "Text Recognition:",
        "image_url": image_url,
    }

    runpod.api_key = args.api_key
    endpoint = runpod.Endpoint(args.endpoint_id)

    print("Sending request to RunPod serverless (sync)...", flush=True)
    try:
        result = endpoint.run_sync(job_input, timeout=args.timeout)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    if isinstance(result, dict):
        status = result.get("status")
        output = result.get("output")
        if status != "COMPLETED":
            print("Response:", json.dumps(result, indent=2, default=str))
            sys.exit(1)
    else:
        output = result

    if output is None:
        print("Empty output.")
        return

    if isinstance(output, dict):
        err = output.get("error")
        if err:
            print(f"Error from handler: {err}", file=sys.stderr)
            sys.exit(1)
        text = output.get("output", "")
    else:
        text = str(output)

    print("--- OCR result ---")
    print(text)
    print("---")
    if isinstance(result, dict) and result.get("executionTime") is not None:
        print(f"Execution time: {result['executionTime']} ms")

    if args.verbose and isinstance(result, dict):
        print("Full response:", json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
