"""Cloud image generation — OpenAI, Google Gemini/Imagen, FAL.ai.

Generates images via cloud APIs. Each provider function handles
authentication, API call, and file saving. The dispatch function
routes to the correct provider.

Currently configured: OpenAI (gpt-image-1.5), Google (Nano Banana + Imagen 4),
FAL.ai (FLUX.2 Pro, FLUX.2 Klein, Ideogram 3.0 via fal.ai),
Recraft V4 raster (1K standard, 2K Pro, 4K via Creative Upscale chain) —
direct API or FAL.
"""

import base64
import functools
import logging
import os
import tempfile
import time
from pathlib import Path

import fal_client
import httpx
import requests
from google import genai
from google.genai.types import GenerateContentConfig, GenerateImagesConfig, ImageConfig
from openai import OpenAI

logger = logging.getLogger(__name__)


# --- Connection-reset retry decorator (Run 6 Finding #16) -------------------
#
# Run 6 dogfood (2026-04-29) hit ConnectionResetError on the 3rd of 4 Phase C
# Pro generations. The orchestrator retried manually; this decorator codifies
# the retry so transient TCP resets do not abort an otherwise-successful run.
# Three attempts with 1s/2s/5s backoff is a routine pattern for third-party
# API resilience — not aggressive enough to mask real outages, but generous
# enough to ride out single-packet drops or brief upstream blips.
#
# The decorator catches ``ConnectionResetError``, ``ConnectionError`` (the
# Python builtin), ``requests.exceptions.ConnectionError`` (the
# library-specific subclass FAL.ai surfaces), and three httpx
# transport-layer failures (``RemoteProtocolError``, ``ConnectError``,
# ``ReadError``) that the google-genai SDK raises when its underlying
# httpx client hits a transient connection drop. It does NOT catch HTTP
# errors (4xx/5xx — see ``httpx.HTTPStatusError`` in the negative test),
# authentication errors, ValueError, or RuntimeError — those are
# deterministic failures that retrying cannot fix.
#
# Issue #72: surfaced 2026-05-07 during the blog-post asset run dogfood
# when a Nano Banana Pro 4K call raised httpx.RemoteProtocolError; the
# original decorator did not include httpx exceptions and the operator
# had to wrap the call in a manual retry loop. See
# docs/superpowers/dogfooding/2026-05-07-blog-post-asset-run.md bug #1.

_RETRYABLE = (
    ConnectionResetError,
    ConnectionError,
    requests.exceptions.ConnectionError,
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadError,
)


def retry_on_connection_reset(
    max_attempts: int = 3,
    backoff_seconds: tuple[float, ...] = (1, 2, 5),
):
    """Decorator that retries on transient connection-reset errors.

    Args:
        max_attempts: Total attempts including the first call.
        backoff_seconds: Seconds to ``time.sleep`` between attempts. Must be
            at least ``max_attempts - 1`` long.

    The wrapped callable is invoked normally on the first attempt; on a
    retryable failure the wrapper sleeps the next backoff value and tries
    again. After ``max_attempts`` failures the last exception is re-raised.
    Non-retryable exceptions propagate immediately.
    """
    if len(backoff_seconds) < max_attempts - 1:
        raise ValueError(
            f"backoff_seconds must have at least max_attempts - 1 = "
            f"{max_attempts - 1} entries, got {len(backoff_seconds)}"
        )

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except _RETRYABLE as exc:
                    if attempt + 1 >= max_attempts:
                        raise
                    delay = backoff_seconds[attempt]
                    logger.warning(
                        "Connection reset on attempt %d/%d for %s: %s. "
                        "Retrying in %ss.",
                        attempt + 1, max_attempts, fn.__name__, exc, delay,
                    )
                    time.sleep(delay)
            # Unreachable — the loop either returns or re-raises.
            raise RuntimeError("retry loop exited without return or raise")
        return wrapper
    return deco


class ProviderNotConfiguredError(Exception):
    """Raised when a cloud provider's credentials are not set."""


class ProviderNotImplementedError(NotImplementedError):
    """Raised when a provider is configured but implementation is pending."""


class ProviderResolutionUnsupportedError(ValueError):
    """Raised when a provider/model combination cannot honour the requested resolution.

    Carries the closest supported tier so callers can retry intelligently.
    """

    def __init__(self, provider, model, requested, supported):
        self.provider = provider
        self.model = model
        self.requested = requested
        self.supported = supported
        super().__init__(
            f"{provider}/{model} does not support resolution={requested!r}. "
            f"Supported: {supported}. Retry with one of those, or pick a "
            f"different model."
        )


# --- Resolution normalisation -----------------------------------------------

_VALID_RESOLUTIONS = ("512", "1K", "2K", "4K")


def _normalise_resolution(resolution):
    """Case-fold and validate a resolution string.

    '1k' -> '1K'.  '512' -> '512'.  '8K' raises ValueError.

    Args:
        resolution: str — one of '512', '1K', '2K', '4K' (case-insensitive
            for the K-suffixed values).

    Returns:
        str: normalised value.

    Raises:
        TypeError: resolution is not a string.
        ValueError: resolution is not one of the recognised values.
    """
    if not isinstance(resolution, str):
        raise TypeError(
            f"resolution must be str, got {type(resolution).__name__}"
        )
    stripped = resolution.strip()
    upper = stripped.upper()
    if upper in {"1K", "2K", "4K"}:
        return upper
    if stripped == "512":
        return "512"
    raise ValueError(
        f"resolution={resolution!r} not recognised. "
        f"Valid values: {_VALID_RESOLUTIONS}"
    )


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


# Google Imagen has dual pricing depending on backend:
#   - Vertex AI (GOOGLE_APPLICATION_CREDENTIALS): flat per-image pricing
#   - Gemini Developer API (GOOGLE_API_KEY only): token-based, 2K is dearer
# Nano Banana Pro/Flash bill identically on both backends (per-image).

# Per-resolution costs (provider-agnostic, used for Nano Banana too).
# Sourced from research May 2026; see EPIC #58 pricing table.
_NANO_BANANA_COSTS = {
    ('gemini-3-pro-image-preview', '1K'): 0.134,
    ('gemini-3-pro-image-preview', '2K'): 0.134,
    ('gemini-3-pro-image-preview', '4K'): 0.24,
    ('gemini-3.1-flash-image-preview', '512'): 0.045,
    ('gemini-3.1-flash-image-preview', '1K'): 0.067,
    ('gemini-3.1-flash-image-preview', '2K'): 0.101,
    ('gemini-3.1-flash-image-preview', '4K'): 0.151,
}

# Imagen Vertex AI flat pricing (per-tier, uniform within tier).
_IMAGEN_VERTEX_COSTS = {
    ('imagen-4.0-fast-generate-001', '1K'): 0.020,
    ('imagen-4.0-generate-001', '1K'): 0.040,
    ('imagen-4.0-generate-001', '2K'): 0.040,
    ('imagen-4.0-ultra-generate-001', '1K'): 0.060,
    ('imagen-4.0-ultra-generate-001', '2K'): 0.060,
}

# Imagen Gemini Developer API token-based pricing.
# 1K matches Vertex flat; 2K is dearer (1680 tokens at the Imagen rate).
_IMAGEN_DEVELOPER_COSTS = {
    ('imagen-4.0-fast-generate-001', '1K'): 0.020,
    ('imagen-4.0-generate-001', '1K'): 0.040,
    ('imagen-4.0-generate-001', '2K'): 0.101,
    ('imagen-4.0-ultra-generate-001', '1K'): 0.060,
    ('imagen-4.0-ultra-generate-001', '2K'): 0.101,  # treat as token-based too
}

# Models that use generate_content API (Nano Banana) vs generate_images API (Imagen 4)
_NANO_BANANA_MODELS = {
    'gemini-3.1-flash-image-preview',
    'gemini-3-pro-image-preview',
}

_IMAGEN_MODELS = {
    'imagen-4.0-generate-001',
    'imagen-4.0-fast-generate-001',
    'imagen-4.0-ultra-generate-001',
}

# Per-model supported resolutions (used by validation and discovery).
_MODEL_RESOLUTIONS = {
    'imagen-4.0-fast-generate-001': ['1K'],
    'imagen-4.0-generate-001': ['1K', '2K'],
    'imagen-4.0-ultra-generate-001': ['1K', '2K'],
    'gemini-3.1-flash-image-preview': ['512', '1K', '2K', '4K'],
    'gemini-3-pro-image-preview': ['1K', '2K', '4K'],
    # Recraft V4 raster (issue #61). 'recraft-v4-*' identifiers are router-side;
    # internal dispatch picks the actual endpoint by tier+resolution.
    'recraft-v4-standard': ['1K'],
    'recraft-v4-pro': ['2K', '4K'],
}


def estimate_google_cost(model='gemini-3.1-flash-image-preview', resolution='1K'):
    """Return estimated USD cost for a Google image generation call.

    For Imagen models, billing depends on which Google backend the SDK uses:
      - GOOGLE_APPLICATION_CREDENTIALS set -> Vertex AI flat per-image
      - GOOGLE_API_KEY only -> Gemini Developer API token-based

    Nano Banana Pro/Flash bill identically across both backends.

    Args:
        model: Google model name.
        resolution: '512' | '1K' | '2K' | '4K' (case-insensitive). Default '1K'.

    Returns:
        float: Estimated cost in USD.

    Raises:
        ValueError: If the model/resolution combination is unknown.
    """
    resolution = _normalise_resolution(resolution)

    if model in _NANO_BANANA_MODELS:
        key = (model, resolution)
        if key not in _NANO_BANANA_COSTS:
            raise ValueError(
                f"Unknown Nano Banana model/resolution: {model}/{resolution}. "
                f"Supported: {sorted(k for k in _NANO_BANANA_COSTS if k[0] == model)}"
            )
        return _NANO_BANANA_COSTS[key]

    if model in _IMAGEN_MODELS:
        # Detect backend: Vertex (ADC) wins over Developer API if both are set.
        backend = (
            'vertex'
            if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            else 'developer'
        )
        table = _IMAGEN_VERTEX_COSTS if backend == 'vertex' else _IMAGEN_DEVELOPER_COSTS
        key = (model, resolution)
        if key not in table:
            raise ValueError(
                f"Unknown Imagen model/resolution: {model}/{resolution} "
                f"(backend={backend}). Check supported_resolutions for this model."
            )
        return table[key]

    raise ValueError(
        f"Unknown Google model: {model}. "
        f"Valid models: {sorted(_NANO_BANANA_MODELS | _IMAGEN_MODELS)}"
    )


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

# FAL FLUX 2 Pro caps at 2048x2048. Higher tiers raise.
_FAL_RESOLUTION_TO_IMAGE_SIZE = {
    'fal-ai/flux-2-pro': {
        '1K': 'landscape_16_9',  # existing preset (~1MP)
        '2K': {'width': 2048, 'height': 2048},
    },
    'fal-ai/flux-2-klein': {
        '1K': 'landscape_16_9',
    },
    'fal-ai/ideogram/v3': {
        '1K': 'landscape_16_9',
    },
}

# Derived from _FAL_RESOLUTION_TO_IMAGE_SIZE so the two tables can never drift.
_FAL_SUPPORTED_RESOLUTIONS = {
    model: list(mapping.keys())
    for model, mapping in _FAL_RESOLUTION_TO_IMAGE_SIZE.items()
}


# --- Recraft V4 raster pricing (FAL.ai parity assumption for upscale) ---
# Generation costs verified 2026-05-07 via fal.ai/models/fal-ai/recraft/v4/*.
# Upscale cost on direct API not surfaced in public docs; assume FAL parity
# ($0.25). RECRAFT_UPSCALE_COST_USD env var overrides if discovered to differ.

_RECRAFT_GENERATION_COSTS = {
    ('standard', '1K'): 0.04,
    ('pro', '2K'): 0.25,
    # 4K is generate-at-2K then upscale chain — see estimate_recraft_cost
}

_RECRAFT_UPSCALE_COST_DEFAULT = 0.25  # FAL parity; override via env

# Recraft V4 raster supported resolutions per tier
_RECRAFT_TIER_RESOLUTIONS = {
    'standard': ['1K'],
    'pro': ['2K', '4K'],  # 4K is upscale-chained on top of 2K Pro
}


def _recraft_upscale_cost():
    """Return the assumed upscale cost; env override allowed for hot-fix.

    Override is only honoured if it parses to a positive float — guards
    against a speaker accidentally pricing a paid API at $0 or negative.
    """
    override = os.environ.get('RECRAFT_UPSCALE_COST_USD')
    if override:
        try:
            value = float(override)
            if value > 0:
                return value
        except ValueError:
            pass
    return _RECRAFT_UPSCALE_COST_DEFAULT


def estimate_recraft_cost(tier='pro', resolution='2K'):
    """Return estimated USD cost for a Recraft V4 raster generation.

    Args:
        tier: 'standard' (1024², $0.04) or 'pro' (2048², $0.25).
        resolution: '1K' | '2K' | '4K'. 4K is a chain: 2K Pro generation
            + Creative Upscale at the parity-assumed cost (overridable via
            RECRAFT_UPSCALE_COST_USD env var).

    Returns:
        float: Estimated cost in USD.

    Raises:
        ValueError: If the tier/resolution combination is invalid.
    """
    resolution = _normalise_resolution(resolution)

    if tier not in _RECRAFT_TIER_RESOLUTIONS:
        raise ValueError(
            f"Unknown Recraft tier: {tier!r}. "
            f"Valid: {list(_RECRAFT_TIER_RESOLUTIONS)}"
        )

    supported = _RECRAFT_TIER_RESOLUTIONS[tier]
    if resolution not in supported:
        raise ValueError(
            f"Recraft {tier} tier does not support resolution={resolution!r}. "
            f"Supported: {supported}. "
            f"For 4K use tier='pro' (chains 2K + Creative Upscale)."
        )

    if resolution == '4K':
        # Chain: 2K Pro generation + Creative Upscale
        return _RECRAFT_GENERATION_COSTS[('pro', '2K')] + _recraft_upscale_cost()

    return _RECRAFT_GENERATION_COSTS[(tier, resolution)]


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

def generate_openai(prompt, output_path, *, resolution='1K', size=None,
                    quality='medium', background='auto', model='gpt-image-1.5'):
    """Generate an image using OpenAI GPT Image API.

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated PNG.
        resolution: '1K' only (gpt-image-1.5 caps at ~1.5MP). '2K'/'4K'/'512'
            raise ProviderResolutionUnsupportedError. Default '1K'.
        size: Explicit dimensions ('1024x1024', '1536x1024', '1024x1536').
            If provided, takes precedence over resolution. If None, derived
            from resolution.
        quality: Quality tier ('low', 'medium', 'high').
        background: Background type ('auto', 'transparent').
        model: Model name.

    Returns:
        dict: {file_path, provider, model_used, cost_usd, status, resolution}

    Raises:
        ProviderNotConfiguredError: If OPENAI_API_KEY is not set.
        ProviderResolutionUnsupportedError: resolution='2K'/'4K'/'512' and
            no explicit size provided.
    """
    if not os.environ.get('OPENAI_API_KEY'):
        raise ProviderNotConfiguredError(
            'OpenAI not configured: OPENAI_API_KEY environment variable is not set. '
            'See research/04-cloud-api-setup-licensing.md section A for setup.'
        )

    resolution = _normalise_resolution(resolution)

    # Validate resolution unless an explicit size is given.
    # When size is explicit, the user's intent overrides resolution semantics
    # — we use the size and log a warning if there's a mismatch.
    if size is None:
        if resolution != '1K':
            raise ProviderResolutionUnsupportedError(
                provider='openai', model=model,
                requested=resolution, supported=['1K'],
            )
        # Default 1K mapping for OpenAI
        size = '1024x1024'
    else:
        if resolution != '1K':
            logger.warning(
                'OpenAI: explicit size=%r overrides resolution=%r; '
                'using size, ignoring resolution. (gpt-image-1.5 caps at 1.5MP.)',
                size, resolution,
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
        'resolution': resolution,
    }


def generate_google(prompt, output_path, **kwargs):
    """Generate an image using Google Nano Banana or Imagen 4 APIs.

    Auth: GOOGLE_API_KEY (Gemini Developer API) or
          GOOGLE_APPLICATION_CREDENTIALS (Vertex AI).

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated PNG.
        **kwargs: Optional arguments:
            model: Model name (default: 'gemini-3.1-flash-image-preview').
            aspect_ratio: Aspect ratio for Imagen 4 (e.g. '16:9', '1:1').
            resolution: '512' | '1K' | '2K' | '4K'. Default '1K'.
                Per-model support varies; see _MODEL_RESOLUTIONS.

    Returns:
        dict: {file_path, provider, model_used, cost_usd, status, resolution}

    Raises:
        ProviderNotConfiguredError: If neither Google auth env var is set.
        ProviderResolutionUnsupportedError: model doesn't support resolution.
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
    resolution = _normalise_resolution(kwargs.get('resolution', '1K'))

    # Validate resolution against per-model capability
    supported = _MODEL_RESOLUTIONS.get(model)
    if supported is None:
        raise ValueError(
            f"Unknown Google model: {model}. "
            f"Valid: {sorted(_NANO_BANANA_MODELS | _IMAGEN_MODELS)}"
        )
    if resolution not in supported:
        raise ProviderResolutionUnsupportedError(
            provider='google', model=model,
            requested=resolution, supported=supported,
        )

    # Build client — use API key if available, otherwise ADC
    client_kwargs = {}
    if api_key:
        client_kwargs['api_key'] = api_key
    client = genai.Client(**client_kwargs)

    if model in _NANO_BANANA_MODELS:
        image_bytes = _generate_via_nano_banana(client, model, prompt, resolution)
    elif model in _IMAGEN_MODELS:
        image_bytes = _generate_via_imagen(client, model, prompt, aspect_ratio, resolution)
    else:
        raise ValueError(
            f"Unknown Google model: {model}. "
            f"Valid models: {sorted(_NANO_BANANA_MODELS | _IMAGEN_MODELS)}"
        )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(image_bytes)

    cost = estimate_google_cost(model=model, resolution=resolution)
    logger.info(
        'Google image generated: %s (model: %s, resolution: %s, cost: $%.3f)',
        output_path, model, resolution, cost,
    )

    return {
        'file_path': str(output_path),
        'provider': 'google',
        'model_used': model,
        'cost_usd': cost,
        'status': 'generated',
        'resolution': resolution,
    }


def _generate_via_nano_banana(client, model, prompt, resolution='1K'):
    """Generate image via Nano Banana (generate_content API) at given resolution.

    Uses PATH-B per spike (docs/spikes/2026-05-02-google-genai-image-config-spike.md):
    typed ImageConfig from google.genai.types.

    Args:
        client: google.genai.Client instance.
        model: 'gemini-3-pro-image-preview' or 'gemini-3.1-flash-image-preview'.
        prompt: text prompt.
        resolution: '512' | '1K' | '2K' | '4K' (must be supported by model).

    Returns:
        bytes: Raw image bytes from the response.

    Raises:
        RuntimeError: If no image part is found in the response.
    """
    config = GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT'],
        image_config=ImageConfig(image_size=resolution),
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


def _generate_via_imagen(client, model, prompt, aspect_ratio, resolution):
    """Generate image via Imagen 4 (generate_images API) at the given resolution.

    Returns:
        bytes: Raw image bytes from the response.
    """
    config = GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio=aspect_ratio,
        output_mime_type='image/png',
        image_size=resolution,
    )
    response = client.models.generate_images(
        model=model,
        prompt=prompt,
        config=config,
    )

    return response.generated_images[0].image.image_bytes


def generate_fal(prompt, output_path, **kwargs):
    """Generate an image using FAL.ai (FLUX.2 Pro, Klein, Ideogram, etc.).

    Auth: FAL_KEY environment variable.

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated PNG.
        **kwargs: Optional arguments:
            model: FAL endpoint (default: 'fal-ai/flux-2-pro').
            resolution: '1K' | '2K' (FLUX 2 Pro caps at 2048x2048; Klein and
                Ideogram support 1K only). Default '1K'.
            image_size: Explicit FAL image_size (preset string OR
                {'width': W, 'height': H} dict). When provided, takes
                precedence over resolution.

    Returns:
        dict: {file_path, provider, model_used, cost_usd, status, resolution}

    Raises:
        ProviderNotConfiguredError: If FAL_KEY is not set.
        ProviderResolutionUnsupportedError: model doesn't support resolution.
    """
    if not os.environ.get('FAL_KEY'):
        raise ProviderNotConfiguredError(
            'FAL.ai not configured: FAL_KEY environment variable is not set. '
            'See research/04-cloud-api-setup-licensing.md section C for setup.'
        )

    model = kwargs.get('model', 'fal-ai/flux-2-pro')
    resolution = _normalise_resolution(kwargs.get('resolution', '1K'))

    # Determine image_size: explicit kwarg wins; otherwise resolve from resolution.
    if 'image_size' in kwargs:
        image_size = kwargs['image_size']
        if resolution != '1K':
            logger.warning(
                'FAL: explicit image_size=%r overrides resolution=%r.',
                image_size, resolution,
            )
    else:
        # Validate the resolution against per-model capability
        supported = _FAL_SUPPORTED_RESOLUTIONS.get(model, ['1K'])
        if resolution not in supported:
            raise ProviderResolutionUnsupportedError(
                provider='fal', model=model,
                requested=resolution, supported=supported,
            )
        # Map resolution -> image_size
        mapping = _FAL_RESOLUTION_TO_IMAGE_SIZE.get(model, {})
        if resolution not in mapping:
            raise ProviderResolutionUnsupportedError(
                provider='fal', model=model,
                requested=resolution, supported=list(mapping.keys()),
            )
        image_size = mapping[resolution]

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
    logger.info(
        'FAL.ai image generated: %s (model: %s, resolution: %s, cost: $%.3f)',
        output_path, model, resolution, cost,
    )

    return {
        'file_path': str(output_path),
        'provider': 'fal',
        'model_used': model,
        'cost_usd': cost,
        'status': 'generated',
        'resolution': resolution,
    }


# --- Recraft V4 raster (direct API) ---

_RECRAFT_DIRECT_BASE_URL = 'https://external.api.recraft.ai/v1'
_RECRAFT_UPSCALE_URL = f'{_RECRAFT_DIRECT_BASE_URL}/images/creativeUpscale'

# Tier -> (size string for Recraft images.generate, native pixel resolution).
_RECRAFT_TIER_TO_SIZE = {
    'standard': '1024x1024',
    'pro': '2048x2048',
}


def generate_recraft_direct(prompt, output_path, *, tier='pro',
                            resolution='2K', colors=None,
                            style='realistic_image', **kwargs):
    """Generate a raster image using the Recraft V4 direct API.

    Uses OpenAI-compatible endpoint at external.api.recraft.ai/v1. For 4K
    output the call is dispatched to `_generate_recraft_direct_with_upscale`,
    which generates at 2K Pro and chains a Creative Upscale call.

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated PNG.
        tier: 'standard' (1024², $0.04) or 'pro' (2048², $0.25 for 2K).
        resolution: '1K' (standard) | '2K' (pro) | '4K' (pro + upscale chain).
        colors: Optional list of RGB dicts for brand palette,
                e.g. [{'rgb': [0, 51, 102]}, {'rgb': [255, 204, 0]}].
        style: Recraft style preset (default 'realistic_image').

    Returns:
        dict: {file_path, provider, tier, resolution, model_used, cost_usd,
               status}.

    Raises:
        ProviderNotConfiguredError: If RECRAFT_API_KEY is not set.
        ProviderResolutionUnsupportedError: If tier doesn't support resolution.
    """
    api_key = os.environ.get('RECRAFT_API_KEY') or os.environ.get('RECRAFT_API')
    if not api_key:
        raise ProviderNotConfiguredError(
            'Recraft not configured: RECRAFT_API_KEY environment variable is '
            'not set. See research/04-cloud-api-setup-licensing.md section D '
            'for setup.'
        )

    resolution = _normalise_resolution(resolution)

    if tier not in _RECRAFT_TIER_RESOLUTIONS:
        raise ValueError(
            f"Unknown Recraft tier: {tier!r}. "
            f"Valid: {list(_RECRAFT_TIER_RESOLUTIONS)}"
        )

    supported = _RECRAFT_TIER_RESOLUTIONS[tier]
    if resolution not in supported:
        raise ProviderResolutionUnsupportedError(
            provider='recraft',
            model=f'recraft-v4-{tier}',
            requested=resolution,
            supported=supported,
        )

    # 4K is generate-at-2K-Pro then Creative Upscale chain.
    if resolution == '4K':
        return _generate_recraft_direct_with_upscale(
            prompt=prompt,
            output_path=output_path,
            api_key=api_key,
            colors=colors,
            style=style,
        )

    # 1K (standard) and 2K (pro) — single generation call.
    client = OpenAI(
        base_url=_RECRAFT_DIRECT_BASE_URL,
        api_key=api_key,
    )

    extra_body = {'response_format': 'url'}
    if colors:
        extra_body['controls'] = {'colors': colors}

    size = _RECRAFT_TIER_TO_SIZE[tier]

    response = client.images.generate(
        prompt=prompt,
        model='recraftv4',
        style=style,
        size=size,
        extra_body=extra_body,
    )

    image_url = response.data[0].url
    r = requests.get(image_url, timeout=30)
    r.raise_for_status()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(r.content)

    cost = estimate_recraft_cost(tier=tier, resolution=resolution)
    logger.info(
        'Recraft V4 raster generated: %s (tier: %s, resolution: %s, cost: $%.3f)',
        output_path, tier, resolution, cost,
    )

    return {
        'file_path': str(output_path),
        'provider': 'recraft',
        'tier': tier,
        'resolution': resolution,
        'model_used': f'recraft-v4-{tier}',
        'cost_usd': cost,
        'status': 'generated',
    }


def _generate_recraft_direct_with_upscale(prompt, output_path, *, api_key,
                                          colors=None,
                                          style='realistic_image'):
    """Chain helper: generate at 2K Pro, then Creative Upscale to 4K.

    Two-step Recraft direct API chain:
      1. images.generate (2K Pro, 2048x2048)
      2. POST /images/creativeUpscale (multipart file upload, Bearer auth)

    The intermediate 2K render is written to a temp file and unlinked in a
    `finally` clause so we don't leak even if the upscale fails.

    Args:
        prompt: Text prompt for image generation.
        output_path: Final 4K PNG destination.
        api_key: Recraft API key (already validated by the caller).
        colors: Optional list of RGB dicts for brand palette.
        style: Recraft style preset (default 'realistic_image').

    Returns:
        dict: Same shape as `generate_recraft_direct`, with resolution='4K'
        and model_used='recraft-v4-pro+upscale'.
    """
    client = OpenAI(
        base_url=_RECRAFT_DIRECT_BASE_URL,
        api_key=api_key,
    )

    extra_body = {'response_format': 'url'}
    if colors:
        extra_body['controls'] = {'colors': colors}

    # Step 1: generate at 2K Pro.
    response = client.images.generate(
        prompt=prompt,
        model='recraftv4',
        style=style,
        size=_RECRAFT_TIER_TO_SIZE['pro'],
        extra_body=extra_body,
    )
    twok_url = response.data[0].url
    twok_response = requests.get(twok_url, timeout=30)
    twok_response.raise_for_status()
    twok_bytes = twok_response.content

    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        Path(tmp_path).write_bytes(twok_bytes)

        # Step 2: Creative Upscale via multipart POST (Bearer auth).
        with open(tmp_path, 'rb') as f:
            upscale_response = requests.post(
                _RECRAFT_UPSCALE_URL,
                headers={'Authorization': f'Bearer {api_key}'},
                files={'file': f},
                timeout=60,
            )
        upscale_response.raise_for_status()
        upscaled_url = upscale_response.json()['image']['url']
        upscaled_response = requests.get(upscaled_url, timeout=30)
        upscaled_response.raise_for_status()
        upscaled_bytes = upscaled_response.content

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(upscaled_bytes)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    cost = estimate_recraft_cost(tier='pro', resolution='4K')
    logger.info(
        'Recraft V4 raster 4K generated via upscale chain: %s (cost: $%.3f)',
        output_path, cost,
    )

    return {
        'file_path': str(output_path),
        'provider': 'recraft',
        'tier': 'pro',
        'resolution': '4K',
        'model_used': 'recraft-v4-pro+upscale',
        'cost_usd': cost,
        'status': 'generated',
    }


# --- Recraft V4 raster (FAL.ai) ---


def generate_recraft_fal(prompt, output_path, *, tier='pro', resolution='2K',
                         colors=None, **kwargs):
    """Generate a raster image using Recraft V4 via FAL.ai.

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated image.
        tier: 'standard' (1024², $0.04) or 'pro' (2048², $0.25).
        resolution: '1K' | '2K' | '4K'.
        colors: Optional list of RGB dicts, e.g. [{'r': 0, 'g': 51, 'b': 102}].

    Returns:
        dict: {file_path, provider, tier, resolution, model_used, cost_usd, status}

    Raises:
        ProviderNotConfiguredError: If FAL_KEY not set.
        ProviderResolutionUnsupportedError: If tier doesn't support resolution.
    """
    if not os.environ.get('FAL_KEY'):
        raise ProviderNotConfiguredError(
            'FAL.ai not configured: FAL_KEY environment variable is not set. '
            'See research/04-cloud-api-setup-licensing.md section C for setup.'
        )

    resolution = _normalise_resolution(resolution)
    supported = _RECRAFT_TIER_RESOLUTIONS.get(tier, [])
    if resolution not in supported:
        raise ProviderResolutionUnsupportedError(
            provider='fal-recraft',
            model=f'recraft-v4-{tier}',
            requested=resolution,
            supported=supported,
        )

    if resolution == '4K':
        return _generate_recraft_fal_with_upscale(prompt, output_path, colors=colors)

    endpoint = (
        'fal-ai/recraft/v4/text-to-image' if tier == 'standard'
        else 'fal-ai/recraft/v4/pro/text-to-image'
    )

    arguments = {'prompt': prompt}
    if colors:
        arguments['colors'] = colors

    result = fal_client.subscribe(endpoint, arguments=arguments)
    image_url = result['images'][0]['url']
    r = requests.get(image_url, timeout=30)
    r.raise_for_status()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(r.content)

    cost = estimate_recraft_cost(tier=tier, resolution=resolution)
    logger.info(
        'FAL Recraft raster generated: %s (tier: %s, resolution: %s, cost: $%.3f)',
        output_path, tier, resolution, cost,
    )

    return {
        'file_path': str(output_path),
        'provider': 'fal-recraft',
        'tier': tier,
        'resolution': resolution,
        'model_used': f'recraft-v4-{tier}',
        'cost_usd': cost,
        'status': 'generated',
    }


def _generate_recraft_fal_with_upscale(prompt, output_path, *, colors=None):
    """4K chain via FAL: 2K Pro generation, then Creative Upscale."""
    arguments = {'prompt': prompt}
    if colors:
        arguments['colors'] = colors

    # 1) Generate at 2K Pro
    gen_result = fal_client.subscribe(
        'fal-ai/recraft/v4/pro/text-to-image',
        arguments=arguments,
    )
    intermediate_url = gen_result['images'][0]['url']

    # 2) Creative Upscale (image_url input form — FAL accepts URL or upload)
    upscale_result = fal_client.subscribe(
        'fal-ai/recraft/upscale/creative',
        arguments={'image_url': intermediate_url},
    )
    upscaled_url = upscale_result['image']['url']

    r = requests.get(upscaled_url, timeout=60)
    r.raise_for_status()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(r.content)

    cost = estimate_recraft_cost(tier='pro', resolution='4K')
    logger.info(
        'FAL Recraft raster generated (4K via upscale): %s (cost: $%.3f)',
        output_path, cost,
    )

    return {
        'file_path': str(output_path),
        'provider': 'fal-recraft',
        'tier': 'pro',
        'resolution': '4K',
        'model_used': 'recraft-v4-pro+upscale',
        'cost_usd': cost,
        'status': 'generated',
    }


# --- Dispatch ---


def _dispatch_recraft(prompt, output_path, **kwargs):
    """Dispatch Recraft to direct API or FAL based on which key is set.

    If the caller didn't specify `tier` but did specify `resolution`, derive
    tier from resolution (1K → standard, 2K/4K → pro). This makes Recraft
    work cleanly through `generate_cloud_image(provider='recraft', resolution='1K')`
    without the caller needing to know about the tier/resolution combination
    matrix.

    Mirrors the icon path's dual-route logic: RECRAFT_API_KEY → direct,
    FAL_KEY → fal. Direct API is preferred when both are set.
    """
    if 'tier' not in kwargs and 'resolution' in kwargs:
        # Auto-pick tier from resolution
        resolution = _normalise_resolution(kwargs['resolution'])
        if resolution == '1K':
            kwargs['tier'] = 'standard'
        elif resolution in ('2K', '4K'):
            kwargs['tier'] = 'pro'
        # else: leave tier unset and let validation in the underlying function
        # surface ProviderResolutionUnsupportedError

    if os.environ.get('RECRAFT_API_KEY') or os.environ.get('RECRAFT_API'):
        return generate_recraft_direct(prompt, output_path, **kwargs)
    return generate_recraft_fal(prompt, output_path, **kwargs)


_PROVIDERS = {
    'openai': generate_openai,
    'google': generate_google,
    'fal': generate_fal,
    'recraft': _dispatch_recraft,
}


@retry_on_connection_reset()
def generate_cloud_image(prompt, provider, output_path, *, resolution='1K', **kwargs):
    """Generate an image using the specified cloud provider at the requested resolution.

    Args:
        prompt: Text prompt for image generation.
        provider: Provider name ('openai', 'google', 'fal', 'recraft').
        output_path: Where to save the generated image.
        resolution: '512' | '1K' | '2K' | '4K' (case-insensitive, default '1K').
            Per-provider/model support varies; ProviderResolutionUnsupportedError
            is raised for unsupported combinations. See provider_discovery for
            per-model capability.
        **kwargs: Provider-specific arguments (size, model, image_size, etc.).
            If a kwarg conflicts with `resolution` semantics, the kwarg wins
            with a logger warning (provider-specific).

    Returns:
        dict: Result from the provider function. Includes 'resolution' field.

    Raises:
        ValueError: If provider is unknown or resolution string is invalid.
        ProviderNotConfiguredError: If provider credentials are missing.
        ProviderResolutionUnsupportedError: provider/model can't honour resolution.

    Connection resilience (Run 6 Finding #16): the dispatcher is wrapped in
    ``retry_on_connection_reset`` so transient TCP resets from third-party
    APIs do not abort the bridge's enrichment cycle. Three attempts with
    1s/2s/5s backoff. Non-connection failures (auth errors, quota limits,
    ValueError, ProviderResolutionUnsupportedError) propagate immediately.
    """
    if provider not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Available: {list(_PROVIDERS)}"
        )
    return _PROVIDERS[provider](
        prompt, output_path, resolution=resolution, **kwargs,
    )
