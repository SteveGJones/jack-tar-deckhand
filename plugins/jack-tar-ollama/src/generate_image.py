#!/usr/bin/env python3
"""Generate an image via Ollama's REST API and save it as PNG."""

import argparse
import base64
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

# Model-aware default timeouts (seconds)
MODEL_TIMEOUTS = {
    "x/z-image-turbo": 120,
    "x/flux2-klein": 600,
}
DEFAULT_TIMEOUT = 300


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an image via Ollama")
    parser.add_argument("--prompt", required=True, help="Text prompt for image generation")
    parser.add_argument("--model", default="x/z-image-turbo", help="Ollama model identifier")
    parser.add_argument("--output", default=None, help="Output file path (default: output/YYYYMMDD-HHMMSS.png)")
    parser.add_argument("--width", type=int, default=1024, help="Image width in pixels")
    parser.add_argument("--height", type=int, default=1024, help="Image height in pixels")
    parser.add_argument("--steps", type=int, default=8, help="Number of inference steps")
    parser.add_argument("--seed", type=int, default=None, help="Seed for reproducibility")
    parser.add_argument("--timeout", type=int, default=None, help="HTTP timeout in seconds (auto-detected from model if not set)")
    return parser.parse_args()


def resolve_output_path(output: str | None) -> Path:
    if output:
        path = Path(output).resolve()
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = Path(f"output/{timestamp}.png").resolve()
    os.makedirs(path.parent, exist_ok=True)
    return path


def resolve_timeout(model: str, explicit_timeout: int | None) -> int:
    if explicit_timeout is not None:
        return explicit_timeout
    base_model = model.split(":")[0]
    return MODEL_TIMEOUTS.get(base_model, DEFAULT_TIMEOUT)


def generate(args: argparse.Namespace) -> None:
    output_path = resolve_output_path(args.output)
    timeout = resolve_timeout(args.model, args.timeout)

    body = {
        "model": args.model,
        "prompt": args.prompt,
        "stream": False,
        "width": args.width,
        "height": args.height,
        "steps": args.steps,
    }
    if args.seed is not None:
        body["seed"] = args.seed

    try:
        resp = requests.post(OLLAMA_URL, json=body, timeout=timeout)
    except requests.ConnectionError:
        print("Ollama is not running. Start it with: ollama serve", file=sys.stderr)
        sys.exit(1)
    except requests.Timeout:
        print(
            f"Generation timed out after {timeout}s. Try reducing --steps or image dimensions.",
            file=sys.stderr,
        )
        sys.exit(1)

    if resp.status_code == 404 or "not found" in resp.text.lower():
        print(f"Model {args.model} not found. Pull it with: ollama pull {args.model}", file=sys.stderr)
        sys.exit(1)

    if resp.status_code != 200:
        print(f"Ollama API error: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
        sys.exit(1)

    if not resp.text or not resp.text.strip():
        print("Ollama returned an empty response. The server may be busy or the request too large.", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    image_b64 = data.get("image")
    if not image_b64:
        print("Ollama returned no image data. The model may not support image generation.", file=sys.stderr)
        sys.exit(1)

    output_path.write_bytes(base64.b64decode(image_b64))
    print(str(output_path))


if __name__ == "__main__":
    generate(parse_args())
