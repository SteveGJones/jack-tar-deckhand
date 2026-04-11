# jack-tar-msft-smartart

Editable PowerPoint SmartArt graphics using native OOXML. Produces SmartArt that speakers can modify — rename nodes, switch layouts, insert images — directly in PowerPoint after delivery.

29 layouts across 9 categories, all MIT-sourced from dotnet/Open-XML-SDK.

## Prerequisites

- Python 3.10+ with python-pptx and lxml

## Skills

| Skill | Purpose |
|-------|---------|
| `/render` | Generate editable SmartArt carrier .pptx from a spec |
| `/inject` | Graft SmartArt from carriers into an assembled deck |
| `/catalog` | List available layouts with capacity and guidance |
| `/verify` | Check dependencies and layout fixture availability |

## Quick Start

```
/jack-tar-msft-smartart:verify
/jack-tar-msft-smartart:catalog
```
