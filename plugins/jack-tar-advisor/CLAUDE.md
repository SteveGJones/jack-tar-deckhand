# jack-tar-advisor

Standalone model advisor. Ask which image models fit your tasks — get evidence-based recommendations covering per-image costs, which external services to pay for, and which local models to install (sizes, RAM requirements, licences).

Works with whatever jack-tar engine plugins are present: it probes live availability (API keys, Ollama, mflux weights, machine RAM) and reads the shared model catalog as its single source of truth — from an installed jack-tar plugin copy, the repo root, or the published remote catalog.

## Skills

| Skill | Purpose |
|-------|---------|
| `/model-advisor` | Per-task model recommendations with cost estimates and install/pay guidance |

## Quick Start

```
/jack-tar-advisor:model-advisor "30 slides/month: hero images + flowcharts, M2 Max 32GB — what do I install, what do I pay for?"
```

Evidence base: the 2026-07-17 blind adversarial model benchmark (`docs/spikes/2026-07-17-mlx-model-benchmark/`), the Ollama↔MLX equivalence spike, the MLX install guide, and the model catalog's per-entry verified notes.
