"""Tests for image cache manager."""

import os
import shutil
import tempfile

import pytest
from PIL import Image


@pytest.fixture
def tmp_cache():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


@pytest.fixture
def test_image(tmp_cache):
    """Create a small test image."""
    path = os.path.join(tmp_cache, 'source.png')
    img = Image.new('RGB', (100, 100), color=(255, 0, 0))
    img.save(path)
    return path


class TestComputeCacheKey:
    def test_returns_64_char_hex(self):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tempfile.mkdtemp())
        key = cache.compute_cache_key('a beautiful sunset', 1920, 1080, 'x/z-image-turbo')
        assert len(key) == 64
        assert all(c in '0123456789abcdef' for c in key)

    def test_same_inputs_same_key(self):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tempfile.mkdtemp())
        k1 = cache.compute_cache_key('sunset', 1920, 1080, 'x/z-image-turbo')
        k2 = cache.compute_cache_key('sunset', 1920, 1080, 'x/z-image-turbo')
        assert k1 == k2

    def test_different_prompt_different_key(self):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tempfile.mkdtemp())
        k1 = cache.compute_cache_key('sunset', 1920, 1080, 'x/z-image-turbo')
        k2 = cache.compute_cache_key('sunrise', 1920, 1080, 'x/z-image-turbo')
        assert k1 != k2

    def test_different_dimensions_different_key(self):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tempfile.mkdtemp())
        k1 = cache.compute_cache_key('sunset', 1920, 1080, 'x/z-image-turbo')
        k2 = cache.compute_cache_key('sunset', 1024, 1024, 'x/z-image-turbo')
        assert k1 != k2

    def test_different_model_different_key(self):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tempfile.mkdtemp())
        k1 = cache.compute_cache_key('sunset', 1920, 1080, 'x/z-image-turbo')
        k2 = cache.compute_cache_key('sunset', 1920, 1080, 'x/flux2-klein')
        assert k1 != k2

    def test_palette_affects_key(self):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tempfile.mkdtemp())
        k1 = cache.compute_cache_key('sunset', 1920, 1080, 'x/z-image-turbo', palette=['1A365D'])
        k2 = cache.compute_cache_key('sunset', 1920, 1080, 'x/z-image-turbo', palette=['FF0000'])
        assert k1 != k2

    def test_palette_order_normalised(self):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tempfile.mkdtemp())
        k1 = cache.compute_cache_key('sunset', 1920, 1080, 'x/z-image-turbo', palette=['AA', 'BB'])
        k2 = cache.compute_cache_key('sunset', 1920, 1080, 'x/z-image-turbo', palette=['BB', 'AA'])
        assert k1 == k2  # sorted, so order doesn't matter


class TestGetPut:
    def test_miss_returns_none(self, tmp_cache):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tmp_cache)
        assert cache.get('nonexistent_key') is None

    def test_put_then_get(self, tmp_cache, test_image):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tmp_cache)
        key = 'test_key_abc123'
        cached_path = cache.put(key, test_image)
        assert os.path.isfile(cached_path)
        result = cache.get(key)
        assert result == cached_path
        assert os.path.isfile(result)

    def test_cached_file_is_copy(self, tmp_cache, test_image):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tmp_cache)
        cached_path = cache.put('key1', test_image)
        # Cached file should be a different path than the source
        assert cached_path != test_image
        # But should have the same content
        with open(test_image, 'rb') as f1, open(cached_path, 'rb') as f2:
            assert f1.read() == f2.read()

    def test_l1_memory_cache(self, tmp_cache, test_image):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tmp_cache)
        cache.put('mem_key', test_image)
        # L1 hit should work even if we delete the index file
        # (because it's in memory)
        result = cache.get('mem_key')
        assert result is not None

    def test_l2_filesystem_persistence(self, tmp_cache, test_image):
        from src.cache_manager import ImageCache
        # Put with one instance
        cache1 = ImageCache(cache_dir=tmp_cache)
        cache1.put('persist_key', test_image)
        # Get with a new instance (L1 is empty, should hit L2)
        cache2 = ImageCache(cache_dir=tmp_cache)
        result = cache2.get('persist_key')
        assert result is not None
        assert os.path.isfile(result)

    def test_put_overwrites_existing(self, tmp_cache, test_image):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tmp_cache)
        cache.put('overwrite_key', test_image)
        # Create a different image
        path2 = os.path.join(tmp_cache, 'other.png')
        Image.new('RGB', (50, 50), color=(0, 255, 0)).save(path2)
        cache.put('overwrite_key', path2)
        result = cache.get('overwrite_key')
        assert result is not None


class TestStats:
    def test_empty_cache(self, tmp_cache):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tmp_cache)
        stats = cache.stats()
        assert stats['total_entries'] == 0
        assert stats['total_size_bytes'] == 0
        assert stats['l1_entries'] == 0

    def test_after_put(self, tmp_cache, test_image):
        from src.cache_manager import ImageCache
        cache = ImageCache(cache_dir=tmp_cache)
        cache.put('stat_key', test_image)
        stats = cache.stats()
        assert stats['total_entries'] == 1
        assert stats['total_size_bytes'] > 0
        assert stats['l1_entries'] == 1
