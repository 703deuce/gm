# handler.py – GLM-OCR RunPod serverless (Transformers, no vLLM)
import os
import base64
from io import BytesIO

import requests
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
import runpod

MODEL_PATH = os.getenv("GLMOCR_MODEL", "zai-org/GLM-OCR")

print("Loading GLM-OCR...")
processor = AutoProcessor.from_pretrained(MODEL_PATH)
model = AutoModelForImageTextToText.from_pretrained(
    pretrained_model_name_or_path=MODEL_PATH,
    torch_dtype="auto",
    device_map="auto",
)
model.eval()
print("GLM-OCR loaded.")


def load_image(inp: dict) -> Image.Image:
    """
    Supports:
      - image_url: http(s) URL or data: URL
      - image_b64: base64-encoded image bytes
    """
    if "image_b64" in inp and inp["image_b64"]:
        data = base64.b64decode(inp["image_b64"])
        return Image.open(BytesIO(data)).convert("RGB")

    url = inp.get("image_url")
    if not url:
        raise ValueError("image_url or image_b64 is required")

    if url.startswith("data:"):
        # data:image/jpeg;base64,...
        header, b64 = url.split(",", 1)
        data = base64.b64decode(b64)
        return Image.open(BytesIO(data)).convert("RGB")

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return Image.open(BytesIO(resp.content)).convert("RGB")


def glm_ocr_infer(prompt: str, image: Image.Image, max_new_tokens: int = 8192) -> str:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "url": "ignored.png"},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    img_inputs = processor(images=image, return_tensors="pt")
    chat_inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )

    inputs = {**img_inputs, **chat_inputs}
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    inputs.pop("token_type_ids", None)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
        )

    input_len = inputs["input_ids"].shape[1]
    output_text = processor.decode(
        generated_ids[0][input_len:],
        skip_special_tokens=False,
    )
    return output_text


def handler(event):
    """
    event["input"]:
      - prompt: e.g. "Text Recognition:" or JSON schema prompt
      - image_url: http(s) or data: URL   OR  image_b64: base64 string
      - max_new_tokens (optional, default 8192)
    """
    inp = event.get("input", {}) or {}
    prompt = inp.get("prompt", "Text Recognition:")
    max_new_tokens = int(inp.get("max_new_tokens", 8192))

    try:
        image = load_image(inp)
    except Exception as e:
        return {"error": f"failed to load image: {e}"}

    try:
        text = glm_ocr_infer(prompt, image, max_new_tokens=max_new_tokens)
    except Exception as e:
        return {"error": f"inference error: {e}"}

    return {"output": text}


runpod.serverless.start({"handler": handler})
