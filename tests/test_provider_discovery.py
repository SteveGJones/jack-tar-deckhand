"""Tests for provider discovery module."""

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
        assert 'google_vertex' in result
        assert 'fal' in result
        assert 'recraft' in result

    def test_all_available(self):
        from src.provider_discovery import discover_providers
        mock_ollama = {'available': True, 'models': ['x/z-image-turbo'], 'endpoint': 'http://localhost:11434'}
        with patch('src.provider_discovery.probe_ollama', return_value=mock_ollama), \
             patch.dict(os.environ, {
                 'OPENAI_API_KEY': 'sk-test',
                 'GOOGLE_CLOUD_PROJECT': 'my-project',
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
