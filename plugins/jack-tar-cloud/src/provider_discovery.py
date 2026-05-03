"""Provider discovery — probe available image generation providers.

Checks which image generation backends are available at pipeline start.
The imagegen-bridge calls this before routing image requests.

Providers:
- Ollama: HTTP health check to localhost:11434, list image models
- OpenAI: OPENAI_API_KEY environment variable
- Google: GOOGLE_API_KEY (Gemini Developer API) or GOOGLE_APPLICATION_CREDENTIALS (Vertex AI)
- FAL.ai: FAL_KEY environment variable
- Recraft: RECRAFT_API_KEY environment variable (configurable via provider_config.json)

Project-level overrides: place a provider_config.json in the project root
to remap env var names. Example:
  {"recraft": {"env_var": "RECRAFT_API"}}
"""

import json
import logging
import os

import requests

logger = logging.getLogger(__name__)

# Known FAL.ai image generation models
_FAL_IMAGE_MODELS = ['flux-2-pro', 'recraft-v4', 'ideogram-3']

# Per-model supported resolutions — exposed via discover_providers().
# Matches _MODEL_RESOLUTIONS in generate_cloud_image.py for Google models;
# mirrors the FAL/OpenAI capability per model.
_PROVIDER_MODEL_RESOLUTIONS = {
    'openai': {
        'gpt-image-1.5': ['1K'],
    },
    'google': {
        'imagen-4.0-fast-generate-001': ['1K'],
        'imagen-4.0-generate-001': ['1K', '2K'],
        'imagen-4.0-ultra-generate-001': ['1K', '2K'],
        'gemini-3.1-flash-image-preview': ['512', '1K', '2K', '4K'],
        'gemini-3-pro-image-preview': ['1K', '2K', '4K'],
    },
    'fal': {
        'fal-ai/flux-2-pro': ['1K', '2K'],
        'fal-ai/flux-2-klein': ['1K'],
        'fal-ai/ideogram/v3': ['1K'],
    },
}

# Default env vars per provider (matches official SDK conventions)
_PROVIDER_DEFAULTS = {
    'openai': {
        'env_var': 'OPENAI_API_KEY',
        'model': 'gpt-image-1.5',
    },
    'google': {
        'env_var': ['GOOGLE_API_KEY', 'GOOGLE_APPLICATION_CREDENTIALS'],
        'model': 'imagen-4',
    },
    'fal': {
        'env_var': 'FAL_KEY',
        'models': _FAL_IMAGE_MODELS,
    },
    'recraft': {
        'env_var': 'RECRAFT_API_KEY',
        'model': 'recraft-v4',
    },
}


def _load_config(config_path):
    """Load project-level provider config, if it exists.

    Args:
        config_path: Path to provider_config.json.

    Returns:
        dict: Config overrides, or empty dict if file missing/invalid.
    """
    if not config_path:
        return {}
    try:
        with open(config_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _resolve_env_vars(provider_name, config):
    """Resolve the env var(s) for a provider, applying config overrides.

    Args:
        provider_name: Provider key (e.g., 'recraft').
        config: Project config overrides dict.

    Returns:
        list[str]: Env var names to check, in priority order.
    """
    defaults = _PROVIDER_DEFAULTS.get(provider_name, {})

    # Config override takes priority
    if provider_name in config:
        override = config[provider_name].get('env_var')
        if override is not None:
            return [override] if isinstance(override, str) else list(override)

    # Fall back to defaults
    default_vars = defaults.get('env_var', [])
    if isinstance(default_vars, str):
        return [default_vars]
    return list(default_vars)


def probe_ollama(endpoint='http://localhost:11434'):
    """Probe Ollama availability and list image-capable models.

    Calls GET {endpoint}/api/tags and filters for models whose names start
    with 'x/' (the Ollama image model naming convention).

    Args:
        endpoint: Base URL for the Ollama service.

    Returns:
        dict: {'available': bool, 'models': list[str], 'endpoint': str}
    """
    url = f'{endpoint}/api/tags'
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        all_models = [m['name'] for m in data.get('models', [])]
        image_models = [name for name in all_models if name.startswith('x/')]
        available = len(image_models) > 0
        return {
            'available': available,
            'models': image_models,
            'endpoint': endpoint,
        }
    except (requests.ConnectionError, requests.Timeout) as exc:
        logger.debug('Ollama not reachable at %s: %s', endpoint, exc)
        return {
            'available': False,
            'models': [],
            'endpoint': endpoint,
        }


def probe_env_provider(env_var, provider_name, model_name):
    """Check if a cloud provider is available via environment variable(s).

    Args:
        env_var: Env var name (str) or list of names to check in order.
        provider_name: Provider name for logging.
        model_name: Default model name if available.

    Returns:
        dict: {'available': bool, 'model': str, 'env_var_found': str|None}
    """
    env_vars = [env_var] if isinstance(env_var, str) else list(env_var)

    for var in env_vars:
        value = os.environ.get(var, '')
        if value:
            return {
                'available': True,
                'model': model_name,
                'env_var_found': var,
            }

    logger.debug(
        'Provider %s not configured: none of %s are set',
        provider_name, env_vars,
    )
    return {
        'available': False,
        'model': model_name,
        'env_var_found': None,
    }


def discover_providers(config_path='provider_config.json'):
    """Probe all providers and return an AvailableProviders dict.

    Args:
        config_path: Optional path to provider_config.json for env var overrides.

    Returns:
        dict: Per-provider availability and capability metadata.
            Each provider entry contains 'available' (bool) plus provider-specific
            fields. For openai/google/fal, a 'models' dict is attached with
            per-model resolution capability after the base probe completes:

            {
                'ollama': {
                    'available': bool,
                    'models': list[str],   # list of installed model name strings
                    'endpoint': str,
                },
                'openai': {
                    'available': bool,
                    'model': str,
                    'env_var_found': str|None,
                    'models': {
                        'gpt-image-1.5': {'supported_resolutions': ['1K']},
                    },
                },
                'google': {
                    'available': bool,
                    'model': str,
                    'env_var_found': str|None,
                    'models': {
                        'imagen-4.0-fast-generate-001': {'supported_resolutions': ['1K']},
                        'imagen-4.0-generate-001': {'supported_resolutions': ['1K', '2K']},
                        'imagen-4.0-ultra-generate-001': {'supported_resolutions': ['1K', '2K']},
                        'gemini-3.1-flash-image-preview': {'supported_resolutions': ['512', '1K', '2K', '4K']},
                        'gemini-3-pro-image-preview': {'supported_resolutions': ['1K', '2K', '4K']},
                    },
                },
                'fal': {
                    'available': bool,
                    'models': {
                        'fal-ai/flux-2-pro': {'supported_resolutions': ['1K', '2K']},
                        'fal-ai/flux-2-klein': {'supported_resolutions': ['1K']},
                        'fal-ai/ideogram/v3': {'supported_resolutions': ['1K']},
                    },
                },
                'recraft': {
                    'available': bool,
                    'model': str,
                    'env_var_found': str|None,
                    # no 'models' key — recraft is not in _PROVIDER_MODEL_RESOLUTIONS
                },
            }

            Note: ollama 'models' is a list[str] of installed model name strings
            (no resolution metadata — Ollama is a local model lister, not a
            resolution-capable cloud provider). Only openai/google/fal gain the
            per-model resolution surface via _PROVIDER_MODEL_RESOLUTIONS.
    """
    config = _load_config(config_path)

    ollama_result = probe_ollama()

    openai_vars = _resolve_env_vars('openai', config)
    openai_result = probe_env_provider(openai_vars, 'openai', 'gpt-image-1.5')

    google_vars = _resolve_env_vars('google', config)
    google_result = probe_env_provider(google_vars, 'google', 'imagen-4')

    recraft_vars = _resolve_env_vars('recraft', config)
    recraft_result = probe_env_provider(recraft_vars, 'recraft', 'recraft-v4')

    # FAL returns a models list rather than a single model name
    fal_vars = _resolve_env_vars('fal', config)
    fal_available = any(bool(os.environ.get(v, '')) for v in fal_vars)
    fal_result = {
        'available': fal_available,
        'models': _FAL_IMAGE_MODELS if fal_available else [],
    }

    result = {
        'ollama': ollama_result,
        'openai': openai_result,
        'google': google_result,
        'fal': fal_result,
        'recraft': recraft_result,
    }

    # Attach per-model resolution capability metadata so callers can filter
    # resolution-tier requests against capability before dispatch.
    for provider_name, models in _PROVIDER_MODEL_RESOLUTIONS.items():
        if provider_name in result:
            result[provider_name]['models'] = {
                model: {'supported_resolutions': resolutions}
                for model, resolutions in models.items()
            }

    return result
