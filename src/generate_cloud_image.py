"""Cloud image generation — OpenAI, Google Gemini/Imagen, FAL.ai.

Generates images via cloud APIs. Each provider function handles
authentication, API call, and file saving. The dispatch function
routes to the correct provider.

Currently configured: OpenAI (gpt-image-1.5), Google (Nano Banana + Imagen 4),
FAL.ai (FLUX.2 Pro, FLUX.2 Klein, Ideogram 3.0 via fal.ai).
"""

import base64
import logging
import os
from pathlib import Path

import fal_client
import requests
from google import genai
from google.genai.types import GenerateContentConfig, GenerateImagesConfig
from openai import OpenAI

logger = logging.getLogger(__name__)


class ProviderNotConfiguredError(Exception):
    """Raised when a cloud provider's credentials are not set."""


class ProviderNotImplementedError(NotImplementedError):
    """Raised when a provider is configured but implementation is pending."""


# --- Cost tables (from research/04-cloud-api-setup-licensing.md) ---

_OPENAI_COSTS = {
    ('1024x1024', 'low'): 0.009,
    ('1024x1024', 'medium'): 0.034,
    ('1024x1024', 'high'): 0.133,
    ('1536x1024', 'low'): 0.013,
    ('1536x1024', 'medium'): 0.051,
    ('1536x1024', 'high'): 0.200,
    ('1024x1536', 'low'): 0.013,
    ('1024x1536', 'medium'): 0.051,
    ('1024x1536', 'high'): 0.200,
}


def estimate_openai_cost(size='1536x1024', quality='medium'):
    """Return estimated USD cost for an OpenAI image generation call.

    Args:
        size: Image size string.
        quality: Quality tier ('low', 'medium', 'high').

    Returns:
        float: Estimated cost in USD.

    Raises:
        ValueError: If the size/quality combination is unknown.
    """
    key = (size, quality)
    if key not in _OPENAI_COSTS:
        raise ValueError(
            f"Unknown size/quality combination: {size}/{quality}. "
            f"Valid combos: {list(_OPENAI_COSTS)}"
        )
    return _OPENAI_COSTS[key]


_GOOGLE_COSTS = {
    'imagen-4.0-fast-generate-001': 0.020,
    'imagen-4.0-generate-001': 0.040,
    'gemini-3.1-flash-image-preview': 0.067,
    'gemini-3-pro-image-preview': 0.134,
}

# Models that use generate_content API (Nano Banana) vs generate_images API (Imagen 4)
_NANO_BANANA_MODELS = {
    'gemini-3.1-flash-image-preview',
    'gemini-3-pro-image-preview',
}

_IMAGEN_MODELS = {
    'imagen-4.0-generate-001',
    'imagen-4.0-fast-generate-001',
}


def estimate_google_cost(model='gemini-3.1-flash-image-preview'):
    """Return estimated USD cost for a Google image generation call.

    Args:
        model: Google model name.

    Returns:
        float: Estimated cost in USD.

    Raises:
        ValueError: If the model is unknown.
    """
    if model not in _GOOGLE_COSTS:
        raise ValueError(
            f"Unknown Google model: {model}. "
            f"Valid models: {list(_GOOGLE_COSTS)}"
        )
    return _GOOGLE_COSTS[model]


# FAL.ai cost data (from research/04-cloud-api-setup-licensing.md)
# FLUX.2 Pro: $0.030 for 1st MP + $0.015 per extra MP (~$0.045 for 1920x1080)
# FLUX.2 Klein: $0.014 flat per image
# Ideogram 3.0: ~$0.030-$0.090 per image (use midpoint $0.060)

_FAL_FLAT_COSTS = {
    'fal-ai/flux-2-klein': 0.014,
    'fal-ai/ideogram/v3': 0.060,
}

# Tiered megapixel models: (base_cost_first_mp, cost_per_extra_mp)
_FAL_TIERED_COSTS = {
    'fal-ai/flux-2-pro': (0.030, 0.015),
}

# Approximate megapixel counts for FAL image_size presets
_FAL_SIZE_MEGAPIXELS = {
    'square_hd': 1.048576,     # 1024x1024
    'square': 1.048576,         # 1024x1024
    'portrait_4_3': 1.048576,   # ~768x1024
    'portrait_16_9': 1.048576,  # ~576x1024 (small) — estimated ~1MP
    'landscape_4_3': 1.398101,  # ~1152x1024 — estimated
    'landscape_16_9': 2.0736,   # ~1920x1080
}

_FAL_FALLBACK_COST = 0.045  # Conservative fallback for unknown models


def estimate_fal_cost(model='fal-ai/flux-2-pro', image_size='landscape_16_9'):
    """Return estimated USD cost for a FAL.ai image generation call.

    FLUX.2 Pro uses tiered pricing: $0.030 for the first megapixel,
    $0.015 per additional megapixel. Klein and Ideogram use flat rates.

    Args:
        model: FAL.ai model endpoint string.
        image_size: FAL.ai image size preset string.

    Returns:
        float: Estimated cost in USD.
    """
    # Flat-rate models
    if model in _FAL_FLAT_COSTS:
        return _FAL_FLAT_COSTS[model]

    # Tiered megapixel models
    if model in _FAL_TIERED_COSTS:
        base_cost, extra_mp_cost = _FAL_TIERED_COSTS[model]
        if isinstance(image_size, dict):
            mp = (image_size['width'] * image_size['height']) / 1_000_000
        else:
            mp = _FAL_SIZE_MEGAPIXELS.get(image_size, 1.5)
        extra_mp = max(0.0, mp - 1.0)
        return round(base_cost + extra_mp * extra_mp_cost, 4)

    # Unknown model — use conservative fallback
    return _FAL_FALLBACK_COST


# --- Provider implementations ---

def generate_openai(prompt, output_path, size='1536x1024', quality='medium',
                    background='auto', model='gpt-image-1.5'):
    """Generate an image using OpenAI GPT Image API.

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated PNG.
        size: Image dimensions ('1024x1024', '1536x1024', '1024x1536').
        quality: Quality tier ('low', 'medium', 'high').
        background: Background type ('auto', 'transparent').
        model: Model name.

    Returns:
        dict: {file_path, provider, model_used, cost_usd, status}

    Raises:
        ProviderNotConfiguredError: If OPENAI_API_KEY is not set.
    """
    if not os.environ.get('OPENAI_API_KEY'):
        raise ProviderNotConfiguredError(
            'OpenAI not configured: OPENAI_API_KEY environment variable is not set. '
            'See research/04-cloud-api-setup-licensing.md section A for setup.'
        )

    output_format = 'png' if background == 'transparent' else 'png'

    client = OpenAI()
    response = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        quality=quality,
        output_format=output_format,
        background=background,
        n=1,
    )

    image_bytes = base64.b64decode(response.data[0].b64_json)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(image_bytes)

    cost = estimate_openai_cost(size=size, quality=quality)
    logger.info('OpenAI image generated: %s (cost: $%.3f)', output_path, cost)

    return {
        'file_path': str(output_path),
        'provider': 'openai',
        'model_used': model,
        'cost_usd': cost,
        'status': 'generated',
    }


def generate_google(prompt, output_path, **kwargs):
    """Generate an image using Google Nano Banana or Imagen 4 APIs.

    Two API paths are supported:
    - Nano Banana models (generate_content API): gemini-3.1-flash-image-preview,
      gemini-3-pro-image-preview
    - Imagen 4 models (generate_images API): imagen-4.0-generate-001,
      imagen-4.0-fast-generate-001

    Auth: GOOGLE_API_KEY (Gemini Developer API) or
          GOOGLE_APPLICATION_CREDENTIALS (Vertex AI).

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated PNG.
        **kwargs: Optional arguments:
            model: Model name (default: 'gemini-3.1-flash-image-preview').
            aspect_ratio: Aspect ratio for Imagen 4 (e.g. '16:9', '1:1').

    Returns:
        dict: {file_path, provider, model_used, cost_usd, status}

    Raises:
        ProviderNotConfiguredError: If neither Google auth env var is set.
    """
    api_key = os.environ.get('GOOGLE_API_KEY')
    has_adc = bool(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))
    if not api_key and not has_adc:
        raise ProviderNotConfiguredError(
            'Google not configured: set GOOGLE_API_KEY (Gemini Developer API) or '
            'GOOGLE_APPLICATION_CREDENTIALS (Vertex AI). '
            'See research/04-cloud-api-setup-licensing.md section B for setup.'
        )

    model = kwargs.get('model', 'gemini-3.1-flash-image-preview')
    aspect_ratio = kwargs.get('aspect_ratio', '16:9')

    # Build client — use API key if available, otherwise ADC
    client_kwargs = {}
    if api_key:
        client_kwargs['api_key'] = api_key
    client = genai.Client(**client_kwargs)

    if model in _NANO_BANANA_MODELS:
        image_bytes = _generate_via_nano_banana(client, model, prompt)
    elif model in _IMAGEN_MODELS:
        image_bytes = _generate_via_imagen(client, model, prompt, aspect_ratio)
    else:
        raise ValueError(
            f"Unknown Google model: {model}. "
            f"Valid models: {sorted(_NANO_BANANA_MODELS | _IMAGEN_MODELS)}"
        )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(image_bytes)

    cost = estimate_google_cost(model=model)
    logger.info('Google image generated: %s (model: %s, cost: $%.3f)', output_path, model, cost)

    return {
        'file_path': str(output_path),
        'provider': 'google',
        'model_used': model,
        'cost_usd': cost,
        'status': 'generated',
    }


def _generate_via_nano_banana(client, model, prompt):
    """Generate image via Nano Banana (generate_content API).

    Returns:
        bytes: Raw image bytes from the response.

    Raises:
        RuntimeError: If no image part is found in the response.
    """
    config = GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT'],
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith('image/'):
            return part.inline_data.data

    raise RuntimeError(
        f'No image data returned from Nano Banana model {model}. '
        'The response contained only text parts.'
    )


def _generate_via_imagen(client, model, prompt, aspect_ratio):
    """Generate image via Imagen 4 (generate_images API).

    Returns:
        bytes: Raw image bytes from the response.
    """
    config = GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio=aspect_ratio,
        output_mime_type='image/png',
    )
    response = client.models.generate_images(
        model=model,
        prompt=prompt,
        config=config,
    )

    return response.generated_images[0].image.image_bytes


def generate_fal(prompt, output_path, **kwargs):
    """Generate an image using FAL.ai (FLUX.2 Pro, Klein, Ideogram, etc.).

    Uses fal_client.subscribe() for synchronous generation. The result
    contains a URL which is downloaded via requests.

    Auth: FAL_KEY environment variable.

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated PNG.
        **kwargs: Optional arguments:
            model: FAL endpoint (default: 'fal-ai/flux-2-pro').
            image_size: FAL size preset (default: 'landscape_16_9').
                Options: 'square_hd', 'square', 'portrait_4_3',
                'portrait_16_9', 'landscape_4_3', 'landscape_16_9',
                or a dict {'width': W, 'height': H}.

    Returns:
        dict: {file_path, provider, model_used, cost_usd, status}

    Raises:
        ProviderNotConfiguredError: If FAL_KEY is not set.
    """
    if not os.environ.get('FAL_KEY'):
        raise ProviderNotConfiguredError(
            'FAL.ai not configured: FAL_KEY environment variable is not set. '
            'See research/04-cloud-api-setup-licensing.md section C for setup.'
        )

    model = kwargs.get('model', 'fal-ai/flux-2-pro')
    image_size = kwargs.get('image_size', 'landscape_16_9')

    result = fal_client.subscribe(model, arguments={
        'prompt': prompt,
        'image_size': image_size,
        'output_format': 'png',
    })

    image_url = result['images'][0]['url']
    response = requests.get(image_url, timeout=30)
    response.raise_for_status()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(response.content)

    cost = estimate_fal_cost(model=model, image_size=image_size)
    logger.info('FAL.ai image generated: %s (model: %s, cost: $%.3f)', output_path, model, cost)

    return {
        'file_path': str(output_path),
        'provider': 'fal',
        'model_used': model,
        'cost_usd': cost,
        'status': 'generated',
    }


# --- Dispatch ---

_PROVIDERS = {
    'openai': generate_openai,
    'google': generate_google,
    'fal': generate_fal,
}


def generate_cloud_image(prompt, provider, output_path, **kwargs):
    """Generate an image using the specified cloud provider.

    Args:
        prompt: Text prompt for image generation.
        provider: Provider name ('openai', 'google', 'fal').
        output_path: Where to save the generated image.
        **kwargs: Provider-specific arguments (size, quality, etc.).

    Returns:
        dict: Result from the provider function.

    Raises:
        ValueError: If provider is unknown.
        ProviderNotConfiguredError: If provider credentials are missing.
    """
    if provider not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Available: {list(_PROVIDERS)}"
        )
    return _PROVIDERS[provider](prompt, output_path, **kwargs)
