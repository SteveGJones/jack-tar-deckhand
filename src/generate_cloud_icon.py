"""Cloud icon generation — Recraft V4 SVG + FAL.ai fallback.

Generates vector icons (SVG) via cloud APIs. Recraft V4 is the primary
provider (only model producing native SVG). FAL.ai hosts Recraft V4
as a fallback endpoint.

Providers:
  - recraft: Recraft V4 direct API (OpenAI-compatible endpoint)
  - fal: Recraft V4 via FAL.ai
"""

import logging
import os
from pathlib import Path

import fal_client
import requests
from openai import OpenAI

logger = logging.getLogger(__name__)


class ProviderNotConfiguredError(Exception):
    """Raised when a cloud provider's credentials are not set."""


class ProviderNotImplementedError(NotImplementedError):
    """Raised when a provider is configured but implementation is pending."""


# --- Cost tables (from research/04-cloud-api-setup-licensing.md) ---

_ICON_COSTS = {
    ('recraft', 'standard'): 0.08,
    ('recraft', 'pro'): 0.30,
    ('fal', 'standard'): 0.08,
    ('fal', 'pro'): 0.30,
}


def estimate_icon_cost(provider='recraft', tier='standard'):
    """Return estimated USD cost for an icon generation call.

    Args:
        provider: Provider name ('recraft', 'fal').
        tier: Quality tier ('standard', 'pro').

    Returns:
        float: Estimated cost in USD.

    Raises:
        ValueError: If the provider/tier combination is unknown.
    """
    key = (provider, tier)
    if key not in _ICON_COSTS:
        raise ValueError(
            f"Unknown provider/tier combination: {provider}/{tier}. "
            f"Valid combos: {list(_ICON_COSTS)}"
        )
    return _ICON_COSTS[key]


# --- Provider implementations ---

def generate_recraft_direct(prompt, output_path, colors=None,
                            output_format='svg', tier='standard', **kwargs):
    """Generate a vector icon using Recraft V4 direct API.

    Uses OpenAI-compatible endpoint at external.api.recraft.ai/v1.

    Args:
        prompt: Text prompt for icon generation.
        output_path: Where to save the SVG/PNG.
        colors: Optional list of RGB dicts for brand palette,
                e.g. [{'rgb': [0, 51, 102]}, {'rgb': [255, 204, 0]}].
        output_format: 'svg' (default) or 'png'.
        tier: 'standard' or 'pro'.

    Returns:
        dict: {file_path, provider, model_used, cost_usd, status, output_format}

    Raises:
        ProviderNotConfiguredError: If RECRAFT_API_KEY / RECRAFT_API is not set.
    """
    api_key = os.environ.get('RECRAFT_API_KEY') or os.environ.get('RECRAFT_API')
    if not api_key:
        raise ProviderNotConfiguredError(
            'Recraft not configured: RECRAFT_API_KEY environment variable is not set. '
            'See research/04-cloud-api-setup-licensing.md section D for setup.'
        )

    client = OpenAI(
        base_url='https://external.api.recraft.ai/v1',
        api_key=api_key,
    )

    # Build controls for Recraft extra_body
    controls = {}
    if colors:
        controls['colors'] = colors

    extra_body = {
        'response_format': 'url',
    }
    if controls:
        extra_body['controls'] = controls

    style = kwargs.get('style', 'vector_illustration')

    response = client.images.generate(
        prompt=prompt,
        model='recraftv4',
        style=style,
        extra_body=extra_body,
    )

    svg_url = response.data[0].url
    r = requests.get(svg_url, timeout=30)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(r.content)

    cost = estimate_icon_cost(provider='recraft', tier=tier)
    logger.info('Recraft icon generated: %s (cost: $%.3f)', output_path, cost)

    return {
        'file_path': str(output_path),
        'provider': 'recraft',
        'model_used': 'recraftv4',
        'cost_usd': cost,
        'status': 'generated',
        'output_format': output_format,
    }


def generate_fal_recraft(prompt, output_path, colors=None,
                         output_format='svg', tier='standard', **kwargs):
    """Generate a vector icon using Recraft V4 via FAL.ai.

    Uses fal-ai/recraft/v4/text-to-vector endpoint.

    Args:
        prompt: Text prompt for icon generation.
        output_path: Where to save the SVG/PNG.
        colors: Optional list of RGB dicts for brand palette,
                e.g. [{'r': 0, 'g': 102, 'b': 204}].
        output_format: 'svg' (default) or 'png'.
        tier: 'standard' or 'pro'.

    Returns:
        dict: {file_path, provider, model_used, cost_usd, status, output_format}

    Raises:
        ProviderNotConfiguredError: If FAL_KEY is not set.
    """
    if not os.environ.get('FAL_KEY'):
        raise ProviderNotConfiguredError(
            'FAL.ai not configured: FAL_KEY environment variable is not set. '
            'See research/04-cloud-api-setup-licensing.md section C for setup.'
        )

    arguments = {
        'prompt': prompt,
        'image_size': 'square_hd',
    }
    if colors:
        arguments['colors'] = colors

    result = fal_client.subscribe(
        'fal-ai/recraft/v4/text-to-vector',
        arguments=arguments,
    )

    svg_url = result['images'][0]['url']
    r = requests.get(svg_url, timeout=30)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(r.content)

    cost = estimate_icon_cost(provider='fal', tier=tier)
    logger.info('FAL Recraft icon generated: %s (cost: $%.3f)', output_path, cost)

    return {
        'file_path': str(output_path),
        'provider': 'fal',
        'model_used': 'recraft-v4',
        'cost_usd': cost,
        'status': 'generated',
        'output_format': output_format,
    }


# --- Dispatch ---

_PROVIDERS = {
    'recraft': generate_recraft_direct,
    'fal': generate_fal_recraft,
}


def generate_cloud_icon(prompt, provider, output_path, **kwargs):
    """Generate a vector icon using the specified cloud provider.

    Args:
        prompt: Text prompt for icon generation.
        provider: Provider name ('recraft', 'fal').
        output_path: Where to save the icon.
        **kwargs: Provider-specific arguments (colors, output_format, tier).

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
