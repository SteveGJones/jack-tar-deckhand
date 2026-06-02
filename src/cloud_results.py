"""GenerationResult — the return value of generate_cloud_image().

Backwards-compatible: implements __fspath__ and __str__ so legacy callers
that pass the result to Path(), open(), or string interpolation keep working.
Also supports dict-style key access so plugin tests that use result['key']
continue to work after the migration from plain-dict returns.

Dict-key compatibility mapping:
  'file_path'  -> self.path      (old dict field name)
  'model_used' -> self.model     (old dict field name)
  'cost_usd'   -> self.cost_estimated  (old dict field name)
  'status'     -> 'generated'    (constant — always succeeded when returned)
  'tier'       -> self.tier      (Recraft-only; None for other providers)
  All other keys are looked up directly as dataclass field names.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GenerationResult:
    path: str
    cost_estimated: float
    cost_actual: Optional[float]
    usage_metadata: Optional[dict]
    provider: str
    model: str
    resolution: str
    tier: Optional[str] = field(default=None)  # Recraft-only

    def __fspath__(self) -> str:
        return self.path

    def __str__(self) -> str:
        return self.path

    # Compatibility shim: plugin tests written against the old dict return
    # shape use result['key'] access.  Map old names to new field names.
    _COMPAT_KEYS = {
        'file_path': 'path',
        'model_used': 'model',
        'cost_usd': 'cost_estimated',
    }

    def __getitem__(self, key: str):
        if key == 'status':
            return 'generated'
        mapped = self._COMPAT_KEYS.get(key, key)
        try:
            return getattr(self, mapped)
        except AttributeError:
            raise KeyError(key) from None
