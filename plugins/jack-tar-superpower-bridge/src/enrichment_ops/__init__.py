"""Per-op enrichment primitives operated against an in-memory Presentation.

The transactional orchestrator (src/enrichment.py) owns save semantics;
each op mutates a `Presentation` in place and lets the orchestrator
decide when (or whether) to write to disk.
"""
