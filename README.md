# GLM-OCR RunPod Serverless Worker

Run [zai-org/GLM-OCR](https://huggingface.co/zai-org/GLM-OCR) on RunPod Serverless using **Transformers** (no vLLM). The model is loaded once on cold start; each job runs inference in-process.

## Structure

- **Dockerfile** – GPU image based on `nvidia/cuda:12.1.0-runtime-ubuntu22.04` + Python, torch, transformers.
- **handler.py** – RunPod worker: loads GLM-OCR once, then handles jobs with `prompt` + `image_url` or `image_b64`.
- **requirements-runpod.txt** – Python deps (runpod, torch, transformers, Pillow, etc.).
- **README.md** – This file.

## Build

```bash
docker build -t glmocr-runpod .
```

## Run locally (optional)

```bash
docker run --gpus all glmocr-runpod
```

## RunPod job input

Send a job with `input` like:

```json
{
  "input": {
    "prompt": "Text Recognition:",
    "image_url": "https://example.com/image.png"
  }
}
```

Or use base64:

```json
{
  "input": {
    "prompt": "Text Recognition:",
    "image_b64": "<base64-encoded image bytes>"
  }
}
```

- **prompt** – Text prompt (default: `"Text Recognition:"`). Also supports `"Table Recognition:"`, `"Formula Recognition:"`, or JSON-schema extraction prompts.
- **image_url** – HTTP(S) URL or `data:image/...;base64,...` data URL. Must be reachable from the container.
- **image_b64** – Alternative: raw base64 string of image bytes.
- **max_new_tokens** – Optional (default: `8192`).

## Response

```json
{
  "output": "<recognized text from GLM-OCR>"
}
```

Errors:

```json
{
  "error": "failed to load image: ..."
}
```
or
```json
{
  "error": "inference error: ..."
}
```

## Environment

- **GLMOCR_MODEL** – Model name (default: `zai-org/GLM-OCR`).

## Notes

- No vLLM or local HTTP server; inference is in-process with Transformers.
- First request after cold start includes model load time; subsequent requests reuse the loaded model.
- Adjust `torch`/`torchvision` in `requirements-runpod.txt` to match your RunPod template’s CUDA if needed.
