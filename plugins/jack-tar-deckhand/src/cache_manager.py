"""Content-addressable image cache for the Jack-Tar Deckhand pipeline.

2-tier cache:
  L1: In-memory dict (fast, per-process)
  L2: Filesystem CAS at ./tmp/cache/images/ with index.json

Cache key = SHA-256 of normalised(prompt + width + height + model + palette_hash).
"""

import hashlib
import json
import os
import shutil


class ImageCache:
    """Content-addressable image cache."""

    def __init__(self, cache_dir='./tmp/cache'):
        """Initialise cache. Creates directories if needed."""
        self._cache_dir = cache_dir
        self._images_dir = os.path.join(cache_dir, 'images')
        self._index_path = os.path.join(cache_dir, 'index.json')

        os.makedirs(self._images_dir, exist_ok=True)

        # L1: in-memory mapping of cache_key -> absolute cached file path
        self._l1 = {}

        # L2: load existing index from disk if present
        if os.path.isfile(self._index_path):
            with open(self._index_path, 'r', encoding='utf-8') as fh:
                self._index = json.load(fh)
        else:
            self._index = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_cache_key(self, prompt, width, height, model, palette=None):
        """Compute a deterministic cache key from generation parameters.

        Args:
            prompt: The generation prompt string.
            width: Image width in pixels.
            height: Image height in pixels.
            model: Model identifier (e.g., 'x/z-image-turbo').
            palette: Optional list of hex colour strings for palette injection.

        Returns:
            str: 64-character hex digest.
        """
        sorted_palette = sorted(palette) if palette else []
        raw = f"{prompt}|{width}|{height}|{model}|{sorted_palette}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def get(self, cache_key):
        """Look up a cached image by key.

        Checks L1 (memory) first, then L2 (filesystem).

        Returns:
            str or None: Path to cached image file, or None if not found.
        """
        # L1 hit
        if cache_key in self._l1:
            return self._l1[cache_key]

        # L2 hit
        if cache_key in self._index:
            rel_path = self._index[cache_key]
            abs_path = os.path.join(self._cache_dir, rel_path)
            if os.path.isfile(abs_path):
                self._l1[cache_key] = abs_path
                return abs_path
            # Index entry points to a missing file — remove stale entry
            del self._index[cache_key]
            self._save_index()

        return None

    def put(self, cache_key, image_path):
        """Store an image in the cache.

        Copies the image file into the cache directory and updates the index.

        Args:
            cache_key: The cache key (from compute_cache_key).
            image_path: Path to the image file to cache.

        Returns:
            str: Path to the cached copy.
        """
        ext = os.path.splitext(image_path)[1] or '.bin'
        prefix = cache_key[:2]
        subdir = os.path.join(self._images_dir, prefix)
        os.makedirs(subdir, exist_ok=True)

        dest_filename = f"{cache_key}{ext}"
        dest_path = os.path.join(subdir, dest_filename)

        shutil.copy2(image_path, dest_path)

        # Relative path stored in index (portable across machines)
        rel_path = os.path.join('images', prefix, dest_filename)
        self._index[cache_key] = rel_path
        self._save_index()

        self._l1[cache_key] = dest_path
        return dest_path

    def stats(self):
        """Return cache statistics.

        Returns:
            dict: {total_entries, total_size_bytes, l1_entries}
        """
        total_size = 0
        for rel_path in self._index.values():
            abs_path = os.path.join(self._cache_dir, rel_path)
            if os.path.isfile(abs_path):
                total_size += os.path.getsize(abs_path)

        return {
            'total_entries': len(self._index),
            'total_size_bytes': total_size,
            'l1_entries': len(self._l1),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _save_index(self):
        """Persist the L2 index to disk."""
        tmp_path = self._index_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as fh:
            json.dump(self._index, fh, indent=2)
        os.replace(tmp_path, self._index_path)
