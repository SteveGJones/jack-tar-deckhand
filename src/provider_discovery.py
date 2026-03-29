"""Provider discovery — probe available image generation providers.

Checks which image generation backends are available at pipeline start.
The imagegen-bridge calls this before routing image requests.

Providers:
- Ollama: HTTP health check to localhost:11434, list image models
- OpenAI: OPENAI_API_KEY environment variable
- Google Vertex AI: GOOGLE_CLOUD_PROJECT environment variable
- FAL.ai: FAL_KEY environment variable
- Recraft: RECRAFT_API_KEY environment variable
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

# Known FAL.ai image generation models
_FAL_IMAGE_MODELS = ['flux-2-pro', 'recraft-v4', 'ideogram-3']


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
    """Check if a cloud provider is available via environment variable.

    Args:
        env_var: Environment variable name to check.
        provider_name: Provider name for logging.
        model_name: Default model name if available.

    Returns:
        dict: {'available': bool, 'model': str}
    """
    value = os.environ.get(env_var, '')
    available = bool(value)
    if not available:
        logger.debug('Provider %s not configured: %s is not set', provider_name, env_var)
    return {
        'available': available,
        'model': model_name,
    }


def discover_providers():
    """Probe all providers and return an AvailableProviders dict.

    Returns:
        dict: {
            'ollama': {'available': bool, 'models': list[str], 'endpoint': str},
            'openai': {'available': bool, 'model': str},
            'google_vertex': {'available': bool, 'model': str},
            'fal': {'available': bool, 'models': list[str]},
            'recraft': {'available': bool, 'model': str},
        }
    """
    ollama_result = probe_ollama()

    openai_result = probe_env_provider('OPENAI_API_KEY', 'openai', 'gpt-image-1.5')
    google_result = probe_env_provider('GOOGLE_CLOUD_PROJECT', 'google_vertex', 'imagen-4')
    recraft_result = probe_env_provider('RECRAFT_API_KEY', 'recraft', 'recraft-v4')

    # FAL returns a models list rather than a single model name
    fal_available = bool(os.environ.get('FAL_KEY', ''))
    fal_result = {
        'available': fal_available,
        'models': _FAL_IMAGE_MODELS if fal_available else [],
    }

    return {
        'ollama': ollama_result,
        'openai': openai_result,
        'google_vertex': google_result,
        'fal': fal_result,
        'recraft': recraft_result,
    }
