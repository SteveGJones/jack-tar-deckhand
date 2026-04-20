"""Tests for provider discovery module."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock


class TestProbeOllama:
    def test_available_with_image_models(self):
        from src.provider_discovery import probe_ollama
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'x/z-image-turbo', 'details': {}},
                {'name': 'x/flux2-klein', 'details': {}},
                {'name': 'llama3.2', 'details': {}},
            ]
        }
        with patch('src.provider_discovery.requests.get', return_value=mock_response):
            result = probe_ollama()
        assert result['available'] is True
        assert 'x/z-image-turbo' in result['models']
        assert 'x/flux2-klein' in result['models']
        assert 'llama3.2' not in result['models']
        assert result['endpoint'] == 'http://localhost:11434'

    def test_unavailable_when_connection_refused(self):
        from src.provider_discovery import probe_ollama
        import requests
        with patch('src.provider_discovery.requests.get', side_effect=requests.ConnectionError):
            result = probe_ollama()
        assert result['available'] is False
        assert result['models'] == []

    def test_unavailable_when_timeout(self):
        from src.provider_discovery import probe_ollama
        import requests
        with patch('src.provider_discovery.requests.get', side_effect=requests.Timeout):
            result = probe_ollama()
        assert result['available'] is False

    def test_unavailable_when_no_image_models(self):
        from src.provider_discovery import probe_ollama
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama3.2', 'details': {}},
                {'name': 'codellama', 'details': {}},
            ]
        }
        with patch('src.provider_discovery.requests.get', return_value=mock_response):
            result = probe_ollama()
        assert result['available'] is False
        assert result['models'] == []

    def test_custom_endpoint(self):
        from src.provider_discovery import probe_ollama
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [{'name': 'x/z-image-turbo', 'details': {}}]
        }
        with patch('src.provider_discovery.requests.get', return_value=mock_response) as mock_get:
            result = probe_ollama(endpoint='http://remote:11434')
        mock_get.assert_called_once_with('http://remote:11434/api/tags', timeout=5)
        assert result['endpoint'] == 'http://remote:11434'


class TestProbeEnvProvider:
    def test_available_when_env_set(self):
        from src.provider_discovery import probe_env_provider
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-123'}):
            result = probe_env_provider('OPENAI_API_KEY', 'openai', 'gpt-image-1.5')
        assert result['available'] is True
        assert result['model'] == 'gpt-image-1.5'

    def test_unavailable_when_env_missing(self):
        from src.provider_discovery import probe_env_provider
        with patch.dict(os.environ, {}, clear=True):
            result = probe_env_provider('OPENAI_API_KEY', 'openai', 'gpt-image-1.5')
        assert result['available'] is False

    def test_unavailable_when_env_empty(self):
        from src.provider_discovery import probe_env_provider
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            result = probe_env_provider('OPENAI_API_KEY', 'openai', 'gpt-image-1.5')
        assert result['available'] is False


class TestDiscoverProviders:
    def test_returns_all_five_providers(self):
        from src.provider_discovery import discover_providers
        with patch('src.provider_discovery.probe_ollama') as mock_ollama, \
             patch.dict(os.environ, {}, clear=True):
            mock_ollama.return_value = {'available': False, 'models': [], 'endpoint': 'http://localhost:11434'}
            result = discover_providers()
        assert 'ollama' in result
        assert 'openai' in result
        assert 'google' in result
        assert 'fal' in result
        assert 'recraft' in result

    def test_all_available(self):
        from src.provider_discovery import discover_providers
        mock_ollama = {'available': True, 'models': ['x/z-image-turbo'], 'endpoint': 'http://localhost:11434'}
        with patch('src.provider_discovery.probe_ollama', return_value=mock_ollama), \
             patch.dict(os.environ, {
                 'OPENAI_API_KEY': 'sk-test',
                 'GOOGLE_API_KEY': 'goog-test',
                 'FAL_KEY': 'fal-test',
                 'RECRAFT_API_KEY': 'rc-test',
             }):
            result = discover_providers()
        assert all(result[p]['available'] for p in result)

    def test_none_available(self):
        from src.provider_discovery import discover_providers
        import requests
        with patch('src.provider_discovery.requests.get', side_effect=requests.ConnectionError), \
             patch.dict(os.environ, {}, clear=True):
            result = discover_providers()
        assert not any(result[p]['available'] for p in result)

    def test_fal_has_models_list(self):
        from src.provider_discovery import discover_providers
        import requests
        with patch('src.provider_discovery.requests.get', side_effect=requests.ConnectionError), \
             patch.dict(os.environ, {'FAL_KEY': 'test-key'}, clear=True):
            result = discover_providers()
        assert result['fal']['available'] is True
        assert isinstance(result['fal']['models'], list)
        assert len(result['fal']['models']) > 0


class TestProbeMultiEnv:
    """Test probing with multiple candidate env vars (first match wins)."""

    def test_first_env_var_found(self):
        from src.provider_discovery import probe_env_provider
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'key-1'}, clear=True):
            result = probe_env_provider(
                ['GOOGLE_API_KEY', 'GOOGLE_APPLICATION_CREDENTIALS'],
                'google', 'imagen-4',
            )
        assert result['available'] is True
        assert result['env_var_found'] == 'GOOGLE_API_KEY'

    def test_second_env_var_found(self):
        from src.provider_discovery import probe_env_provider
        with patch.dict(os.environ, {'GOOGLE_APPLICATION_CREDENTIALS': '/path/key.json'}, clear=True):
            result = probe_env_provider(
                ['GOOGLE_API_KEY', 'GOOGLE_APPLICATION_CREDENTIALS'],
                'google', 'imagen-4',
            )
        assert result['available'] is True
        assert result['env_var_found'] == 'GOOGLE_APPLICATION_CREDENTIALS'

    def test_none_found(self):
        from src.provider_discovery import probe_env_provider
        with patch.dict(os.environ, {}, clear=True):
            result = probe_env_provider(
                ['GOOGLE_API_KEY', 'GOOGLE_APPLICATION_CREDENTIALS'],
                'google', 'imagen-4',
            )
        assert result['available'] is False

    def test_single_string_still_works(self):
        from src.provider_discovery import probe_env_provider
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test'}, clear=True):
            result = probe_env_provider('OPENAI_API_KEY', 'openai', 'gpt-image-1.5')
        assert result['available'] is True
        assert result['env_var_found'] == 'OPENAI_API_KEY'


class TestGoogleDiscovery:
    """Google has two auth paths: API key (Gemini) or ADC (Vertex AI)."""

    def test_available_via_api_key(self):
        from src.provider_discovery import discover_providers
        with patch('src.provider_discovery.probe_ollama',
                   return_value={'available': False, 'models': [], 'endpoint': 'http://localhost:11434'}), \
             patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}, clear=True):
            result = discover_providers()
        assert result['google']['available'] is True
        assert result['google']['env_var_found'] == 'GOOGLE_API_KEY'

    def test_available_via_adc(self):
        from src.provider_discovery import discover_providers
        with patch('src.provider_discovery.probe_ollama',
                   return_value={'available': False, 'models': [], 'endpoint': 'http://localhost:11434'}), \
             patch.dict(os.environ, {'GOOGLE_APPLICATION_CREDENTIALS': '/path/key.json'}, clear=True):
            result = discover_providers()
        assert result['google']['available'] is True

    def test_not_available_without_any_key(self):
        from src.provider_discovery import discover_providers
        with patch('src.provider_discovery.probe_ollama',
                   return_value={'available': False, 'models': [], 'endpoint': 'http://localhost:11434'}), \
             patch.dict(os.environ, {}, clear=True):
            result = discover_providers()
        assert result['google']['available'] is False


class TestRecraftDefault:
    """Default env var is RECRAFT_API_KEY (matching Recraft docs)."""

    def test_detects_recraft_api_key(self):
        from src.provider_discovery import discover_providers
        with patch('src.provider_discovery.probe_ollama',
                   return_value={'available': False, 'models': [], 'endpoint': 'http://localhost:11434'}), \
             patch.dict(os.environ, {'RECRAFT_API_KEY': 'rc-key'}, clear=True):
            result = discover_providers()
        assert result['recraft']['available'] is True


class TestGoogleTiers:
    """Google provider discovery should report all available tiers."""

    def test_google_tiers_when_available(self):
        from src.provider_discovery import discover_providers
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            result = discover_providers(config_path=None)
        google = result['google']
        assert google['available'] is True
        assert 'tiers' in google
        tiers = google['tiers']
        assert 'nanobanana_flash' in tiers
        assert tiers['nanobanana_flash']['model'] == 'gemini-3.1-flash-image-preview'
        assert tiers['nanobanana_flash']['cost'] == 0.067
        assert 'nanobanana_pro' in tiers
        assert tiers['nanobanana_pro']['model'] == 'gemini-3-pro-image-preview'
        assert tiers['nanobanana_pro']['cost'] == 0.134
        assert 'imagen_fast' in tiers
        assert tiers['imagen_fast']['model'] == 'imagen-4.0-fast-generate-001'
        assert tiers['imagen_fast']['cost'] == 0.020
        assert 'imagen_standard' in tiers
        assert tiers['imagen_standard']['model'] == 'imagen-4.0-generate-001'
        assert tiers['imagen_standard']['cost'] == 0.040

    def test_google_tiers_empty_when_unavailable(self):
        from src.provider_discovery import discover_providers
        env = {k: '' for k in ['GOOGLE_API_KEY', 'GOOGLE_APPLICATION_CREDENTIALS',
                                'OPENAI_API_KEY', 'FAL_KEY', 'RECRAFT_API_KEY']}
        with patch.dict(os.environ, env, clear=False):
            for k in env:
                os.environ.pop(k, None)
            result = discover_providers(config_path=None)
        google = result['google']
        assert google['available'] is False
        assert google.get('tiers', {}) == {}

    def test_google_backward_compat_available_and_model_fields(self):
        """Existing code reads google['available'] and google['model'] — keep them."""
        from src.provider_discovery import discover_providers
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            result = discover_providers(config_path=None)
        google = result['google']
        assert google['available'] is True
        assert 'model' in google  # backward compat


class TestProjectConfig:
    """Project config file overrides default env var names."""

    def test_config_overrides_recraft_env_var(self, tmp_path):
        from src.provider_discovery import discover_providers
        config = {'recraft': {'env_var': 'RECRAFT_API'}}
        config_path = tmp_path / 'provider_config.json'
        config_path.write_text(json.dumps(config))

        with patch('src.provider_discovery.probe_ollama',
                   return_value={'available': False, 'models': [], 'endpoint': 'http://localhost:11434'}), \
             patch.dict(os.environ, {'RECRAFT_API': 'my-key'}, clear=True):
            result = discover_providers(config_path=str(config_path))
        assert result['recraft']['available'] is True
        assert result['recraft']['env_var_found'] == 'RECRAFT_API'

    def test_config_overrides_google_env_var(self, tmp_path):
        from src.provider_discovery import discover_providers
        config = {'google': {'env_var': 'MY_GOOGLE_KEY'}}
        config_path = tmp_path / 'provider_config.json'
        config_path.write_text(json.dumps(config))

        with patch('src.provider_discovery.probe_ollama',
                   return_value={'available': False, 'models': [], 'endpoint': 'http://localhost:11434'}), \
             patch.dict(os.environ, {'MY_GOOGLE_KEY': 'custom'}, clear=True):
            result = discover_providers(config_path=str(config_path))
        assert result['google']['available'] is True

    def test_missing_config_file_uses_defaults(self):
        from src.provider_discovery import discover_providers
        with patch('src.provider_discovery.probe_ollama',
                   return_value={'available': False, 'models': [], 'endpoint': 'http://localhost:11434'}), \
             patch.dict(os.environ, {'RECRAFT_API_KEY': 'rc-key'}, clear=True):
            result = discover_providers(config_path='/nonexistent/path.json')
        assert result['recraft']['available'] is True

    def test_config_adds_extra_env_vars(self, tmp_path):
        """Config can add alternative env var names to the defaults."""
        from src.provider_discovery import discover_providers
        config = {'recraft': {'env_var': ['RECRAFT_API_KEY', 'RECRAFT_API']}}
        config_path = tmp_path / 'provider_config.json'
        config_path.write_text(json.dumps(config))

        with patch('src.provider_discovery.probe_ollama',
                   return_value={'available': False, 'models': [], 'endpoint': 'http://localhost:11434'}), \
             patch.dict(os.environ, {'RECRAFT_API': 'alt-key'}, clear=True):
            result = discover_providers(config_path=str(config_path))
        assert result['recraft']['available'] is True
        assert result['recraft']['env_var_found'] == 'RECRAFT_API'
