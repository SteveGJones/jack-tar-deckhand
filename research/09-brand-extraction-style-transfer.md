# Brand Extraction & Style Transfer from Minimal Input

**Research Date:** 2026-03-29
**Context:** Jack-Tar Deckhand — Claude Code skills for conference-quality PowerPoint presentations. The slide-stylist skill must derive a complete design system (palette, fonts, visual tone) from minimal user input — often just a logo image and company name.

---

## 1. Logo-to-Palette Algorithm

### 1.1 Dominant Colour Extraction with ColorThief

The [color-thief-py](https://github.com/fengsp/color-thief-py) library (MIT license, Pillow-based) uses the Modified Median Cut Quantization (MMCQ) algorithm from the Leptonica library to extract dominant colours from images.

**API:**

```python
from colorthief import ColorThief

ct = ColorThief("logo.png")

# Get single dominant colour
dominant = ct.get_color(quality=1)  # Returns (r, g, b) tuple
# quality: int (default 10). 1 = highest quality, slower

# Get full palette
palette = ct.get_palette(color_count=6, quality=1)
# color_count: int (default 10), max palette size
# Returns: list of (r, g, b) tuples
```

**Algorithm internals:** The MMCQ algorithm represents colours in a 3D RGB space, recursively splits the space along the median of the longest dimension (via `VBox` objects), and uses a `PQueue` priority queue to select the next box to split. The `CMap` class stores the final quantized colour map.

**Performance variant:** [fast-colorthief](https://github.com/bedapisl/fast-colorthief) provides a C++ backend for significantly faster processing using the same MMCQ algorithm.

Sources:
- [color-thief-py GitHub](https://github.com/fengsp/color-thief-py)
- [fast-colorthief GitHub](https://github.com/bedapisl/fast-colorthief)

### 1.2 Colour Harmony Derivation

From a single extracted brand colour, derive full palettes using HSL hue rotation. The mathematical formulas for each scheme type:

| Scheme | Hue Offsets | Colours Generated |
|--------|------------|-------------------|
| Complementary | +180 deg | 1 |
| Analogous | +30 deg, -30 deg | 2 |
| Triadic | +120 deg, -120 deg | 2 |
| Split-Complementary | +150 deg, +210 deg | 2 |
| Tetradic (Rectangle) | +60 deg, +180 deg, +240 deg | 3 |

**Python implementation using stdlib `colorsys`:**

```python
import colorsys

def hex_to_hls(hex_color: str) -> tuple[float, float, float]:
    """Convert #RRGGBB to HLS (hue 0-1, lightness 0-1, saturation 0-1)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)

def hls_to_hex(h: float, l: float, s: float) -> str:
    """Convert HLS back to #RRGGBB."""
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

def complementary(hex_color: str) -> str:
    h, l, s = hex_to_hls(hex_color)
    return hls_to_hex((h + 0.5) % 1.0, l, s)

def analogous(hex_color: str) -> list[str]:
    h, l, s = hex_to_hls(hex_color)
    return [
        hls_to_hex((h + 30/360) % 1.0, l, s),
        hls_to_hex((h - 30/360) % 1.0, l, s),
    ]

def triadic(hex_color: str) -> list[str]:
    h, l, s = hex_to_hls(hex_color)
    return [
        hls_to_hex((h + 120/360) % 1.0, l, s),
        hls_to_hex((h - 120/360) % 1.0, l, s),
    ]

def split_complementary(hex_color: str) -> list[str]:
    h, l, s = hex_to_hls(hex_color)
    return [
        hls_to_hex((h + 150/360) % 1.0, l, s),
        hls_to_hex((h + 210/360) % 1.0, l, s),
    ]
```

**Library alternative:** The [colorharmonies](https://pypi.org/project/colorharmonies/) library provides ready-made functions:

```python
from colorharmonies import Color, complementaryColor, triadicColor
from colorharmonies import splitComplementaryColor, analogousColor
from colorharmonies import monochromaticColor

brand = Color([0, 45, 114], "", "")  # RGB input as list
comp = complementaryColor(brand)       # Returns [r, g, b]
triads = triadicColor(brand)           # Returns [[r,g,b], [r,g,b]]
splits = splitComplementaryColor(brand) # Returns [[r,g,b], [r,g,b]]
analogs = analogousColor(brand)         # Returns [[r,g,b], [r,g,b]]
monos = monochromaticColor(brand)       # Returns 9 shades/tints
```

Note: The colorharmonies library is archived (read-only since April 2020) and accepts only RGB list input, no hex strings. For production use, the stdlib `colorsys` approach above is recommended.

Sources:
- [Color Harmony Math (dev.to)](https://dev.to/madsstoumann/colors-are-math-how-they-match-and-how-to-build-a-color-picker-4ei8)
- [colorharmonies PyPI](https://pypi.org/project/colorharmonies/)
- [Color Theory in Python (Things Grow)](https://thingsgrow.me/2020/01/02/navigating-through-000000-and-ffffff-color-theory-in-python/)

### 1.3 WCAG AA Accessible Contrast Pairing

WCAG 2.0 AA requires a contrast ratio of at least **4.5:1** for normal text and **3:1** for large text (18pt+ or 14pt+ bold).

**Formula:** `contrast = (L1 + 0.05) / (L2 + 0.05)` where L1 is the relative luminance of the lighter colour and L2 is the relative luminance of the darker colour.

```python
import wcag_contrast_ratio as contrast

# Input: normalized RGB tuples (0.0 to 1.0)
brand_primary = (0.0, 0.176, 0.447)  # #002D72
white = (1.0, 1.0, 1.0)

ratio = contrast.rgb(brand_primary, white)  # Returns: float (e.g., 12.3)
passes = contrast.passes_AA(ratio)          # Returns: True/False
passes_aaa = contrast.passes_AAA(ratio)     # Returns: True/False
```

**Automated text colour selection:**

```python
def choose_text_color(background_hex: str) -> str:
    """Return black or white depending on which has better contrast."""
    r, g, b = (int(background_hex.lstrip('#')[i:i+2], 16) / 255.0
               for i in (0, 2, 4))
    bg = (r, g, b)
    white_ratio = contrast.rgb((1.0, 1.0, 1.0), bg)
    black_ratio = contrast.rgb(bg, (0.0, 0.0, 0.0))
    return "#ffffff" if white_ratio > black_ratio else "#000000"
```

Sources:
- [wcag-contrast-ratio PyPI](https://pypi.org/project/wcag-contrast-ratio/)
- [ZugBahnHof/color-contrast GitHub](https://github.com/ZugBahnHof/color-contrast)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

### 1.4 Safe Neutral Derivation

Derive light and dark backgrounds that work with the brand palette:

```python
def derive_neutrals(brand_hex: str) -> dict:
    """Generate safe neutral backgrounds from a brand colour."""
    h, l, s = hex_to_hls(brand_hex)
    return {
        "background_light": hls_to_hex(h, 0.97, s * 0.08),  # Near-white tinted
        "background_dark": hls_to_hex(h, 0.12, s * 0.15),   # Near-black tinted
        "surface_light": hls_to_hex(h, 0.93, s * 0.06),     # Card/panel light
        "surface_dark": hls_to_hex(h, 0.18, s * 0.12),      # Card/panel dark
        "text_primary_on_light": hls_to_hex(h, 0.13, s * 0.20),
        "text_secondary_on_light": hls_to_hex(h, 0.40, s * 0.10),
        "text_primary_on_dark": hls_to_hex(h, 0.93, s * 0.05),
        "text_secondary_on_dark": hls_to_hex(h, 0.65, s * 0.08),
    }
```

The approach: keep the brand hue but dramatically reduce saturation and push lightness to extremes. This creates neutrals that are visually "warm" or "cool" in sympathy with the brand, rather than generic grey.

Sources:
- [distinctipy PyPI](https://pypi.org/project/distinctipy/)
- [Python Color Theme Generation (Medium)](https://fuyenh.medium.com/python-generated-color-themes-for-design-system-b5029ab8077f)

### 1.5 Delta-E 2000 Brand Colour Matching

The [colour-science](https://pypi.org/project/colour-science/) library (v0.4.7, BSD-3-Clause, Python 3.11-3.14) provides perceptually accurate colour difference calculations across 90+ RGB colourspaces.

```python
import colour
import numpy as np

def brand_color_distance(hex1: str, hex2: str) -> float:
    """Calculate Delta-E 2000 perceptual distance between two hex colours."""
    rgb1 = np.array([int(hex1.lstrip('#')[i:i+2], 16) / 255.0 for i in (0,2,4)])
    rgb2 = np.array([int(hex2.lstrip('#')[i:i+2], 16) / 255.0 for i in (0,2,4)])

    lab1 = colour.XYZ_to_Lab(colour.sRGB_to_XYZ(rgb1))
    lab2 = colour.XYZ_to_Lab(colour.sRGB_to_XYZ(rgb2))

    return colour.delta_E(lab1, lab2, method='CIE 2000')

# Delta-E interpretation:
# < 1.0  - Not perceptible by human eye
# 1-2    - Perceptible through close observation
# 2-10   - Perceptible at a glance
# 11-49  - Colours are more similar than opposite
# 100    - Colours are exact opposite
```

Available Delta-E methods: `CIE 1976`, `CIE 1994`, `CIE 2000`, `CMC`, `CAM02-LCD`, `CAM02-SCD`, `CAM02-UCS`, `CAM16-LCD`, `CAM16-SCD`, `CAM16-UCS`, `DIN99`, `HyAB`, `HyCH`.

Sources:
- [colour-science PyPI](https://pypi.org/project/colour-science/)
- [colour.delta_E docs](https://colour.readthedocs.io/en/latest/generated/colour.delta_E.html)
- [Delta E Color Difference (DeepWiki)](https://deepwiki.com/colour-science/colour/5.1-delta-e-color-difference)

### 1.6 The 60-30-10 Rule for Slide Palettes

The 60-30-10 rule divides colour usage into three proportions:

| Role | Percentage | Slide Application | Typical Colour |
|------|-----------|-------------------|----------------|
| **Dominant** | 60% | Slide background, large areas | Neutral/light (white, light grey, or tinted neutral) |
| **Secondary** | 30% | Headers, charts, key visuals | Brand primary colour |
| **Accent** | 10% | CTAs, highlights, emphasis | Brand accent / complementary |

For presentations specifically:
- **60%** = Clean neutral background to focus on content
- **30%** = Bold dark text and supporting visuals (charts, images)
- **10%** = Vibrant accent for headers and key emphasis points

Sources:
- [60-30-10 Rule (Medium/UX Collective)](https://uxdesign.cc/how-the-60-30-10-rule-saved-the-day-934e1ee3fdd8)
- [60-30-10 Rule (Wix)](https://www.wix.com/wixel/resources/60-30-10-color-rule)
- [NN/g Color in Design](https://www.nngroup.com/articles/color-enhance-design/)

---

## 2. Company/Topic to Font Suggestion Heuristics

### 2.1 Industry-to-Font Mapping

| Industry/Tone | Heading Font | Body Font | Rationale |
|---------------|-------------|-----------|-----------|
| **Tech / SaaS** | Inter | Inter | Geometric sans, optimized for screens, variable weight |
| **Tech / Startup** | Space Grotesk | Space Mono | AI/crypto aesthetic, technical precision |
| **Finance / Corporate** | Montserrat | Source Sans Pro | Strong geometric headers + clean scannable body |
| **Finance / Traditional** | Roboto | Open Sans | Stable, predictable, universally readable |
| **Creative / Agency** | Playfair Display | Raleway | Serif drama balanced with sans minimalism |
| **Creative / Modern** | Syne Bold | Syne Normal | Variable weight for expressive, unified look |
| **Elegant / Luxury** | Cormorant Garamond | Raleway | Literary tone with practical flow |
| **Elegant / Landing** | Prata | Manrope Light | Soft sophistication |
| **Bold / Impact** | Bebas Neue | Heebo | All-caps impact with friendly curves |
| **Friendly / Education** | Aboreto | Gotu | Whimsical without wildness |
| **Accessibility** | Atkinson Hyperlegible | Inter | Character distinction without UI compromise |
| **Multilingual** | Noto Sans | Noto Serif | 1,000+ languages supported |
| **Data-Heavy** | IBM Plex Sans | IBM Plex Serif | Technical credibility, excellent for tables |

Sources:
- [Best Google Font Pairings 2025 (Medium/Bootcamp)](https://medium.com/design-bootcamp/best-google-font-pairings-for-ui-design-in-2025-ba8d006aa03d)
- [Font Pairings by Industry (K Design Co.)](https://kdesign.co/blog/font-pairings-by-industry-10-designer-approved-combos-that-just-work/)
- [Fonts for Startups (Mojomox)](https://fonts.mojomox.com/blogs/on-type/fonts-for-startups)
- [Figma Font Pairings](https://www.figma.com/resource-library/font-pairings/)

### 2.2 Font Pairing Rules

1. **Maximum two font families** per presentation. A single variable-weight family also works well.
2. **Contrast without clashing** — one display/heading font + one body font with different personalities but compatible geometry.
3. **Variable fonts preferred** — reduce load times by bundling multiple styles in one file (e.g., Inter Variable, Roboto Flex).
4. **x-height matters** — taller x-heights (Inter, Open Sans, Merriweather) read better on projection screens.

### 2.3 Projection Screen Readability

| Element | Minimum Size | Recommended Size |
|---------|-------------|-----------------|
| Title/Heading | 36pt | 40-44pt |
| Body/Bullets | 18pt | 24-28pt |
| Labels/Captions | 14pt | 18pt |
| Conference/Large Venue | 30pt minimum | 34pt+ |

**The 6-10 foot rule:** If you cannot comfortably read your slide from 6-10 feet away on your monitor, the font size is too small for projection.

**The 8H rule:** Text height should be at least 1 inch on screen for every 15 feet of viewing distance.

Sources:
- [Beautiful.ai Font Size Guide](https://www.beautiful.ai/blog/what-font-size-is-best-for-presentations)
- [Presentation Guild 8H Rule](https://www.presentationguild.org/articles/how-big-big-enough-the-8h-rule-reveals-all)
- [Slidor Minimum Font Size](https://www.slidor.agency/blog/quelle-taille-de-police-minimum-pour-powerpoint)

---

## 3. AI Generation Brand Colour Enforcement

### 3.1 Model-by-Model Colour Control Comparison

| Model | Colour Input Method | Accuracy | Notes |
|-------|-------------------|----------|-------|
| **Recraft V3/V4** | `colors: string[]` API parameter | **High** — native hex support | Best-in-class; dedicated `colors` array parameter accepts hex codes directly |
| **Ideogram 3.0** | `color_palette` API parameter | **High** — weighted hex support | Supports preset names OR custom hex+weight members |
| **FLUX.2 Pro/Max** | Hex codes in prompt text + JSON | **High** — "exact accuracy" claimed | Hex in prompt; JSON structure for complex palettes; verify for critical work |
| **GPT Image 1.5** | Natural language + hex in prompt | **Good** — responds better to colour names | "deep navy blue similar to #1B2C40" format; hex control + logo preservation |
| **Gemini 3 Pro** | Reference images (up to 14) | **Moderate** — indirect colour control | No explicit hex parameter; use colour-matched reference images instead |
| **NumColor (FLUX plugin)** | Learned colour embeddings | **4-9x improvement** over baseline | Research framework; 55.7% accuracy vs 13.8% baseline on coarse colours |

### 3.2 Recraft API — Native Colour Palette

```python
import httpx

response = httpx.post(
    "https://external.api.recraft.ai/v1/images/generations",
    headers={"Authorization": f"Bearer {RECRAFT_API_KEY}"},
    json={
        "prompt": "Professional business presentation background with geometric patterns",
        "style": "digital_illustration",
        "colors": ["#002D72", "#FFFFFF", "#F5A623"],  # Brand hex codes
        "size": "1920x1080",
    }
)
```

Recraft V3/V4 is the only major model with a dedicated `colors` array parameter at the API level. Raster styles cost $0.04/image; vector styles $0.08/image.

Sources:
- [Recraft API Documentation](https://www.recraft.ai/docs/api-reference/getting-started)
- [Recraft Color Blog](https://www.recraft.ai/blog/how-to-generate-ai-images-in-specific-colors)
- [Recraft V3 on fal.ai](https://fal.ai/models/fal-ai/recraft/v3/text-to-image)

### 3.3 Ideogram 3.0 — Weighted Colour Palette

```python
# Preset palette
color_palette = {"name": "ULTRAMARINE"}
# Available presets: EMBER, FRESH, JUNGLE, MAGIC, MELON, MOSAIC, PASTEL, ULTRAMARINE

# Custom palette with weights
color_palette = {
    "members": [
        {"color_hex": "#002D72", "color_weight": 0.5},  # Primary, dominant
        {"color_hex": "#FFFFFF", "color_weight": 0.3},   # Secondary
        {"color_hex": "#F5A623", "color_weight": 0.1},   # Accent
    ]
}
# Weights range: 0.05 to 1.0 (inclusive)
# Recommendation: weights should descend from highest to lowest

# Style control options
style_type = "AUTO"  # AUTO | GENERAL | REALISTIC | DESIGN | FICTION
style_codes = ["XXXXXXXX"]  # 8-char hex codes from Random generation
# NOTE: style_codes cannot be used with style_reference_images or style_type
```

Ideogram also supports up to 50+ style presets including `OIL_PAINTING`, `WATERCOLOR`, `RETRO_ETCHING`, `SURREAL_COLLAGE`, and more.

Sources:
- [Ideogram 3.0 API Docs](https://developer.ideogram.ai/api-reference/api-reference/generate-v3)
- [Ideogram Color Palette Docs](https://docs.ideogram.ai/using-ideogram/generation-settings/color-palette)

### 3.4 FLUX.2 — JSON Prompt Format

```json
{
  "brand_colors": {
    "primary": "#6366F1",
    "secondary": "#06B6D4",
    "accent": "#F97316",
    "background": "#F8FAFC",
    "text": "#1E293B"
  },
  "subject": "product packaging mockup",
  "apply_colors": {
    "packaging": "primary",
    "label_text": "text",
    "background": "background",
    "highlight_elements": "accent"
  }
}
```

FLUX.2 matches specified hex codes with high accuracy. Best practice: always use full 6-character format (`#FFFFFF`, not `#FFF`), always include the hash prefix, and associate colours with specific objects rather than vague references.

Sources:
- [FLUX.2 Prompting Guide (RenderFire)](https://renderfire.com/blog/flux-2-prompting-guide)
- [FLUX.2 Prompting Guide (Black Forest Labs)](https://docs.bfl.ai/guides/prompting_guide_flux2)
- [Higgsfield FLUX 2 Intro](https://higgsfield.ai/flux-2-intro)

### 3.5 NumColor — Research Framework for Exact Colour Control

[NumColor](https://arxiv.org/html/2510.20586) is a research framework that addresses the fundamental problem: text encoders fragment hex codes like `#FF5733` into meaningless subword tokens (`#`, `FF`, `57`, `33`), preventing models from understanding the colour specification (baseline accuracy below 15%).

**Key components:**
- **Color Token Aggregator (CTA):** Character-level sequence labeler that detects and unifies fragmented colour tokens using convolutional layers and transformer encoders.
- **ColorBook:** Learnable codebook of 6,707 colour embeddings anchored in CIE Lab space. Uses soft interpolation to map any colour to the text embedding space.

**Results:** 4-9x improvement in numeric colour accuracy; FLUX baseline 13.82% to NumColor 55.71% on coarse colours. Overhead: <2ms per prompt, 115MB additional GPU memory.

Transfers zero-shot across FLUX, Stable Diffusion 3/3.5, PixArt-alpha/Sigma, Sana, and CogView4.

Sources:
- [NumColor Paper (arXiv)](https://arxiv.org/html/2510.20586)
- [GenColorBench Benchmark](https://arxiv.org/html/2510.20586)

### 3.6 Post-Generation Colour Correction with Pillow

When AI-generated images have approximate but not exact brand colours, use post-processing:

```python
from PIL import Image
import numpy as np

def enforce_brand_colors(
    image_path: str,
    brand_colors: list[tuple[int, int, int]],
    tolerance: int = 40
) -> Image.Image:
    """Replace approximate colours with exact brand colours using
    nearest-neighbour matching in RGB space."""
    img = Image.open(image_path).convert("RGB")
    data = np.array(img)

    for target in brand_colors:
        target_arr = np.array(target)
        # Find pixels within tolerance of the target
        distances = np.sqrt(np.sum((data.astype(float) - target_arr) ** 2, axis=2))
        mask = distances < tolerance
        data[mask] = target_arr

    return Image.fromarray(data)

# More sophisticated: map specific source→target colour pairs
def color_channel_remap(
    img: Image.Image,
    source_hex: str,
    target_hex: str,
    tolerance: int = 30
) -> Image.Image:
    """Remap a specific colour region to an exact brand colour."""
    data = np.array(img)
    source = np.array([int(source_hex.lstrip('#')[i:i+2], 16) for i in (0,2,4)])
    target = np.array([int(target_hex.lstrip('#')[i:i+2], 16) for i in (0,2,4)])

    distances = np.sqrt(np.sum((data.astype(float) - source) ** 2, axis=2))
    mask = distances < tolerance

    # Smooth blending at edges
    blend = np.clip(1.0 - distances / tolerance, 0, 1)[..., np.newaxis]
    blended = data * (1 - blend * mask[..., np.newaxis]) + target * blend * mask[..., np.newaxis]

    return Image.fromarray(blended.astype(np.uint8))
```

**Pillow colour tools:**
- `ImageOps.colorize()` — maps grayscale to two/three colours (black→colour1, white→colour2)
- `Image.point()` — per-channel transforms (e.g., scale green by 1.2x)
- `Image.convert("RGB", matrix=...)` — colour channel transformation matrix
- `ImageCms` module — ICC profile-based transforms via LittleCMS2

Sources:
- [Pillow Color Replacement (GitHub Gist)](https://gist.github.com/namieluss/c3fcec0b11d28e5d479c441ece1e7429)
- [Pillow ImageColor Docs](https://pillow.readthedocs.io/en/stable/reference/ImageColor.html)
- [Pillow Color Management (DeepWiki)](https://deepwiki.com/python-pillow/Pillow/2.5-color-management)

---

## 4. Style Reference Image Generation

### 4.1 The Mood Board Approach

Generate one defining style reference image from palette + font + tone, then use it as the visual anchor for all subsequent images in the deck. Around 10 high-resolution reference images is generally sufficient to produce a consistent moodboard, though starting from a single strong reference works for presentations.

**Strategy for presentation decks:**
1. Generate a single "hero" style reference from the brand palette using Recraft or FLUX with exact colours
2. Use that reference for all subsequent image generations via model-specific reference features
3. Validate colour consistency via Delta-E 2000 checks against the brand palette

Sources:
- [Midjourney Moodboards Guide (Chase Jarvis)](https://chasejarvis.com/blog/how-to-control-midjourney-style-references-image-references-and-moodboards/)
- [Higgsfield Moodboards](https://higgsfield.ai/blog/create-custom-ai-moodboard-soul-2)

### 4.2 FLUX Kontext — Multi-Reference Consistency

FLUX.1 Kontext performs in-context image generation by prompting with both text and images. The Style Reference feature generates novel scenes while preserving the unique style of a reference image.

**API (via fal.ai):**

```python
import fal_client

result = fal_client.subscribe(
    "fal-ai/flux-pro/kontext",
    arguments={
        "prompt": "Professional slide background with geometric patterns, brand consistent",
        "image_url": "https://example.com/style_reference.png",  # Reference image
        "guidance_scale": 7.5,
        "num_inference_steps": 28,
        "seed": 42,  # For reproducibility
        "output_format": "png",
    }
)
```

- **Standard endpoint:** 1 reference image (primary editing use case)
- **Multi-image variant** (`kontext_multi`): Up to 10 reference images for character/style consistency
- **Pricing:** Fixed $0.04 per image edit, commercial usage included
- **Strength:** Robust consistency across multiple successive edits with minimal visual drift

Sources:
- [FLUX.1 Kontext Pro (fal.ai)](https://fal.ai/models/fal-ai/flux-pro/kontext)
- [FLUX.1 Kontext (Black Forest Labs)](https://bfl.ai/announcements/flux-1-kontext)
- [FLUX Kontext (Together AI)](https://www.together.ai/blog/flux-1-kontext)
- [Multi-Image Reference Guide (CometAPI)](https://www.cometapi.com/multi-image-reference-with-flux-1-kontext/)

### 4.3 Ideogram Style Codes

Ideogram's style codes are **8-character hexadecimal codes** that capture the visual aesthetic of a generated image. When using the Random style option, each generated image receives a unique style code that can be reused with new prompts to maintain consistent aesthetics.

```python
# Generate with captured style code
response = ideogram_client.generate(
    prompt="Corporate presentation title slide",
    style_codes=["A1B2C3D4", "E5F6A7B8"],  # Reuse captured codes
    # Cannot combine with style_reference_images or style_type
)
```

- Ideogram's Random style explores from a library of **4.3 billion presets**
- Up to **3 reference images** for custom style creation
- Style references available in v3.0 models with AUTO, GENERAL, REALISTIC, and DESIGN modes
- Custom styles are permanent — reference images cannot be changed after creation

Sources:
- [Ideogram Style Docs](https://docs.ideogram.ai/using-ideogram/ideogram-features/style)
- [Ideogram Style Reference](https://docs.ideogram.ai/using-ideogram/features-and-tools/reference-features/style-reference)

### 4.4 Gemini — 14 Reference Image System

Google's Gemini 3 series supports up to **14 reference images** divided into two categories:

**Gemini 3.1 Flash Image Preview:**
- Object Fidelity: up to 10 images (products, logos — preserves colour, shape, texture, logo placement)
- Character Consistency: up to 4 images (faces, hairstyles, clothing across scenes)

**Gemini 3 Pro Image Preview:**
- Object Fidelity: up to 6 images
- Character Consistency: up to 5 images (total: 11 images)

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key="YOUR_API_KEY")

# Reference images passed as array elements alongside text prompt
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        "Generate a presentation slide background matching these brand elements",
        brand_logo_image,       # Object fidelity reference
        style_reference_image,  # Additional reference
    ],
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
    ),
)
```

Note: "Character consistency is not always perfect between input images and generated output images" — small-batch testing recommended before bulk generation.

Sources:
- [Gemini 14 Reference Images Guide (Apiyi)](https://help.apiyi.com/en/gemini-14-reference-images-object-fidelity-character-consistency-guide-en.html)
- [Gemini Image API Guide (LaoZhang)](https://blog.laozhang.ai/en/posts/gemini-image-api-guide-2026)
- [Google Gemini Image Generation Docs](https://ai.google.dev/gemini-api/docs/image-generation)

---

## 5. Corporate Template Ingestion

### 5.1 Extract Palette from PPTX Theme

Theme colours in PPTX files live in the XML at `<a:theme>/<a:themeElements>/<a:clrScheme>`. The DrawingML namespace is `http://schemas.openxmlformats.org/drawingml/2006/main`.

```python
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from lxml import etree

def extract_theme_colors(pptx_path: str) -> dict[str, str]:
    """Extract all theme colours from a PPTX file as hex strings."""
    prs = Presentation(pptx_path)

    # Navigate to theme XML via slide master
    slide_master = prs.slide_masters[0]
    theme_part = slide_master.part.part_related_by(RT.THEME)
    theme_xml = etree.fromstring(theme_part.blob)

    nsmap = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}

    color_names = [
        'dk1', 'lt1', 'dk2', 'lt2',
        'accent1', 'accent2', 'accent3', 'accent4', 'accent5', 'accent6',
        'hlink', 'folHlink'
    ]

    colors = {}
    for name in color_names:
        # Try srgbClr first (direct RGB hex)
        xpath = f'a:themeElements/a:clrScheme/a:{name}/a:srgbClr/@val'
        result = theme_xml.xpath(xpath, namespaces=nsmap)
        if result:
            colors[name] = f"#{result[0]}"
        else:
            # Fall back to sysClr (system colour reference)
            xpath = f'a:themeElements/a:clrScheme/a:{name}/a:sysClr/@lastClr'
            result = theme_xml.xpath(xpath, namespaces=nsmap)
            if result:
                colors[name] = f"#{result[0]}"

    return colors
    # Returns e.g.: {'dk1': '#000000', 'lt1': '#FFFFFF', 'accent1': '#002D72', ...}
```

Sources:
- [python-pptx Issue #308 (Theme RGB)](https://github.com/scanny/python-pptx/issues/308)
- [python-pptx Issue #917 (Change Theme Colors)](https://github.com/scanny/python-pptx/issues/917)
- [MSO_THEME_COLOR_INDEX Docs](https://python-pptx.readthedocs.io/en/latest/api/enum/MsoThemeColorIndex.html)

### 5.2 Extract Font Families from PPTX

```python
from pptx import Presentation
from lxml import etree

def extract_theme_fonts(pptx_path: str) -> dict[str, str]:
    """Extract heading and body font families from the PPTX theme."""
    prs = Presentation(pptx_path)

    slide_master = prs.slide_masters[0]
    theme_part = slide_master.part.part_related_by(RT.THEME)
    theme_xml = etree.fromstring(theme_part.blob)

    nsmap = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}

    fonts = {}

    # Major font = headings
    major = theme_xml.xpath(
        'a:themeElements/a:fontScheme/a:majorFont/a:latin/@typeface',
        namespaces=nsmap
    )
    if major:
        fonts['heading'] = major[0]

    # Minor font = body
    minor = theme_xml.xpath(
        'a:themeElements/a:fontScheme/a:minorFont/a:latin/@typeface',
        namespaces=nsmap
    )
    if minor:
        fonts['body'] = minor[0]

    return fonts
    # Returns e.g.: {'heading': 'Calibri Light', 'body': 'Calibri'}
```

### 5.3 Identify Layout Patterns

```python
def extract_layouts(pptx_path: str) -> list[dict]:
    """Extract all slide layout names and their placeholder structure."""
    prs = Presentation(pptx_path)

    layouts = []
    for layout in prs.slide_layouts:
        placeholders = []
        for ph in layout.placeholders:
            placeholders.append({
                "idx": ph.placeholder_format.idx,
                "name": ph.name,
                "type": str(ph.placeholder_format.type),
                "left": ph.left,
                "top": ph.top,
                "width": ph.width,
                "height": ph.height,
            })
        layouts.append({
            "name": layout.name,
            "placeholders": placeholders,
        })

    return layouts
```

**Font inheritance hierarchy:** Slide placeholder inherits from layout placeholder (by `idx`), which inherits from master placeholder (by type). All formatting properties cascade: position, size, fill, line, and font.

### 5.4 Write Theme Colours Back

To modify theme colours in an existing template:

```python
from lxml.etree import tostring

def set_theme_colors(pptx_path: str, output_path: str, new_colors: dict):
    """Update theme colours in a PPTX file via direct XML manipulation."""
    prs = Presentation(pptx_path)

    slide_master = prs.slide_masters[0]
    theme_part = slide_master.part.part_related_by(RT.THEME)
    theme_xml = etree.fromstring(theme_part.blob)

    nsmap = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}

    for color_name, hex_value in new_colors.items():
        hex_val = hex_value.lstrip('#')
        xpath = f'a:themeElements/a:clrScheme/a:{color_name}/a:srgbClr'
        elements = theme_xml.xpath(xpath, namespaces=nsmap)
        if elements:
            elements[0].set('val', hex_val)
        else:
            # Create srgbClr element if it doesn't exist
            parent_xpath = f'a:themeElements/a:clrScheme/a:{color_name}'
            parents = theme_xml.xpath(parent_xpath, namespaces=nsmap)
            if parents:
                # Remove existing child (e.g., sysClr)
                for child in list(parents[0]):
                    parents[0].remove(child)
                new_elem = etree.SubElement(
                    parents[0],
                    '{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr'
                )
                new_elem.set('val', hex_val)

    theme_part._blob = tostring(theme_xml)
    prs.save(output_path)
```

Sources:
- [python-pptx Issue #917 (XML manipulation approach)](https://github.com/scanny/python-pptx/issues/917)
- [python-pptx Slides API](https://python-pptx.readthedocs.io/en/latest/api/slides.html)
- [python-pptx Placeholders](https://python-pptx.readthedocs.io/en/latest/user/placeholders-using.html)

---

## 6. The StyleGuide Data Contract

### 6.1 Complete JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StyleGuide",
  "description": "Complete design system specification produced by slide-stylist",
  "type": "object",
  "required": ["palette", "fonts", "spacing", "metadata"],
  "properties": {
    "palette": {
      "type": "object",
      "description": "Brand colour palette following the 60-30-10 rule",
      "required": ["primary", "secondary", "accent", "background", "surface", "text_primary", "text_secondary"],
      "properties": {
        "primary":        { "type": "string", "pattern": "^#[0-9a-fA-F]{6}$", "description": "Brand primary colour (30% secondary role)" },
        "secondary":      { "type": "string", "pattern": "^#[0-9a-fA-F]{6}$", "description": "Brand secondary / complementary" },
        "accent":         { "type": "string", "pattern": "^#[0-9a-fA-F]{6}$", "description": "Highlight/CTA colour (10% accent role)" },
        "background":     { "type": "string", "pattern": "^#[0-9a-fA-F]{6}$", "description": "Slide background (60% dominant role)" },
        "surface":        { "type": "string", "pattern": "^#[0-9a-fA-F]{6}$", "description": "Card/panel/container background" },
        "text_primary":   { "type": "string", "pattern": "^#[0-9a-fA-F]{6}$", "description": "Main body text — WCAG AA against background" },
        "text_secondary": { "type": "string", "pattern": "^#[0-9a-fA-F]{6}$", "description": "Secondary/caption text" },
        "text_on_primary":{ "type": "string", "pattern": "^#[0-9a-fA-F]{6}$", "description": "Text on primary colour backgrounds" },
        "chart_colors":   { "type": "array", "items": { "type": "string", "pattern": "^#[0-9a-fA-F]{6}$" }, "minItems": 4, "maxItems": 8, "description": "Chart/graph data series colours" }
      }
    },
    "fonts": {
      "type": "object",
      "required": ["heading", "body"],
      "properties": {
        "heading": { "type": "string", "description": "Heading/title font family name (Google Font)" },
        "body":    { "type": "string", "description": "Body/paragraph font family name (Google Font)" },
        "mono":    { "type": "string", "description": "Monospace font for code/data (optional)", "default": "Roboto Mono" },
        "heading_weight": { "type": "string", "enum": ["300", "400", "500", "600", "700", "800", "900"], "default": "700" },
        "body_weight":    { "type": "string", "enum": ["300", "400", "500", "600", "700"], "default": "400" }
      }
    },
    "spacing": {
      "type": "object",
      "description": "Layout spacing in inches (for 13.333 x 7.5 inch widescreen slides)",
      "properties": {
        "margin_x":    { "type": "number", "description": "Left/right margin in inches", "default": 0.75 },
        "margin_y":    { "type": "number", "description": "Top/bottom margin in inches", "default": 0.5 },
        "gutter":      { "type": "number", "description": "Space between columns/elements in inches", "default": 0.25 },
        "line_height":    { "type": "number", "description": "Line height multiplier", "default": 1.2 },
        "paragraph_spacing": { "type": "number", "description": "Space after paragraphs in points", "default": 12 }
      }
    },
    "font_sizes": {
      "type": "object",
      "description": "Font sizes in points for projection readability",
      "properties": {
        "title":      { "type": "integer", "default": 40, "description": "Slide title" },
        "subtitle":   { "type": "integer", "default": 28, "description": "Slide subtitle" },
        "heading":    { "type": "integer", "default": 32, "description": "Section heading" },
        "body":       { "type": "integer", "default": 22, "description": "Body text / bullets" },
        "caption":    { "type": "integer", "default": 16, "description": "Captions and labels" },
        "footnote":   { "type": "integer", "default": 12, "description": "Source citations" }
      }
    },
    "tone": {
      "type": "object",
      "description": "Visual tone metadata for AI image generation prompts",
      "properties": {
        "industry":   { "type": "string", "description": "Detected or specified industry vertical" },
        "mood":       { "type": "string", "enum": ["formal", "modern", "startup", "elegant", "bold", "friendly", "technical"], "description": "Visual mood/personality" },
        "image_style":{ "type": "string", "enum": ["photorealistic", "illustration", "flat_design", "abstract", "minimal", "corporate"], "description": "Preferred AI image generation style" }
      }
    },
    "ai_generation": {
      "type": "object",
      "description": "Parameters for AI image generation brand enforcement",
      "properties": {
        "recraft_colors":  { "type": "array", "items": { "type": "string" }, "description": "Hex array for Recraft API colors parameter" },
        "ideogram_palette": { "type": "object", "description": "Ideogram color_palette parameter (preset name or members)" },
        "flux_color_json":  { "type": "object", "description": "FLUX.2 JSON prompt colour structure" },
        "style_reference_url": { "type": "string", "format": "uri", "description": "URL of generated style reference image" },
        "ideogram_style_codes": { "type": "array", "items": { "type": "string", "pattern": "^[0-9a-fA-F]{8}$" }, "description": "Captured Ideogram style codes for reuse" }
      }
    },
    "brand_assets": {
      "type": "object",
      "description": "Paths to brand asset files",
      "properties": {
        "logo_path":       { "type": "string", "description": "Path to logo image file" },
        "logo_placement":  { "type": "string", "enum": ["top-left", "top-right", "bottom-left", "bottom-right", "center"], "default": "bottom-right" },
        "style_reference": { "type": "string", "description": "Path to mood board / style reference image" },
        "template_path":   { "type": "string", "description": "Path to source PPTX template (if provided)" }
      }
    },
    "contrast_validation": {
      "type": "object",
      "description": "Pre-computed WCAG contrast ratios for key pairings",
      "properties": {
        "text_on_background":  { "type": "number", "description": "Contrast ratio: text_primary on background" },
        "text_on_surface":     { "type": "number", "description": "Contrast ratio: text_primary on surface" },
        "text_on_primary":     { "type": "number", "description": "Contrast ratio: text_on_primary on primary" },
        "passes_AA":           { "type": "boolean", "description": "All key pairings pass WCAG AA" }
      }
    },
    "metadata": {
      "type": "object",
      "required": ["source", "generated_at"],
      "properties": {
        "source":        { "type": "string", "enum": ["logo_extraction", "template_ingestion", "manual", "company_lookup"], "description": "How the style guide was derived" },
        "company_name":  { "type": "string" },
        "generated_at":  { "type": "string", "format": "date-time" },
        "confidence":    { "type": "number", "minimum": 0, "maximum": 1, "description": "Confidence in extracted palette accuracy" }
      }
    }
  }
}
```

### 6.2 Example StyleGuide Instance

```json
{
  "palette": {
    "primary": "#002D72",
    "secondary": "#4A90D9",
    "accent": "#F5A623",
    "background": "#F8F9FA",
    "surface": "#FFFFFF",
    "text_primary": "#1A1A2E",
    "text_secondary": "#6B7280",
    "text_on_primary": "#FFFFFF",
    "chart_colors": ["#002D72", "#4A90D9", "#F5A623", "#2ECC71", "#E74C3C", "#9B59B6"]
  },
  "fonts": {
    "heading": "Montserrat",
    "body": "Source Sans Pro",
    "mono": "Roboto Mono",
    "heading_weight": "700",
    "body_weight": "400"
  },
  "spacing": {
    "margin_x": 0.75,
    "margin_y": 0.5,
    "gutter": 0.25,
    "line_height": 1.2,
    "paragraph_spacing": 12
  },
  "font_sizes": {
    "title": 40,
    "subtitle": 28,
    "heading": 32,
    "body": 22,
    "caption": 16,
    "footnote": 12
  },
  "tone": {
    "industry": "finance",
    "mood": "formal",
    "image_style": "corporate"
  },
  "ai_generation": {
    "recraft_colors": ["#002D72", "#4A90D9", "#F5A623", "#F8F9FA"],
    "ideogram_palette": {
      "members": [
        {"color_hex": "#002D72", "color_weight": 0.5},
        {"color_hex": "#4A90D9", "color_weight": 0.3},
        {"color_hex": "#F5A623", "color_weight": 0.1}
      ]
    },
    "flux_color_json": {
      "brand_colors": {
        "primary": "#002D72",
        "secondary": "#4A90D9",
        "accent": "#F5A623",
        "background": "#F8F9FA"
      }
    },
    "style_reference_url": null,
    "ideogram_style_codes": []
  },
  "brand_assets": {
    "logo_path": "assets/acme-logo.png",
    "logo_placement": "bottom-right",
    "style_reference": null,
    "template_path": null
  },
  "contrast_validation": {
    "text_on_background": 15.2,
    "text_on_surface": 16.8,
    "text_on_primary": 12.3,
    "passes_AA": true
  },
  "metadata": {
    "source": "logo_extraction",
    "company_name": "Acme Financial",
    "generated_at": "2026-03-29T10:30:00Z",
    "confidence": 0.85
  }
}
```

### 6.3 Generation Pipeline

```
User Input                StyleGuide Output
──────────                ────────────────
Logo image ──────┐
                 ├──→ [ColorThief] ──→ palette.primary, palette.secondary
Company name ────┤
                 ├──→ [Industry Mapper] ──→ fonts.heading, fonts.body, tone.*
                 ├──→ [Harmony Engine] ──→ palette.accent, palette.chart_colors
                 ├──→ [Neutral Deriver] ──→ palette.background, palette.surface
                 ├──→ [WCAG Checker] ──→ palette.text_*, contrast_validation.*
                 └──→ [AI Gen Config] ──→ ai_generation.*

PPTX template ──────→ [Template Ingestor] ──→ (overrides all above)
                         ├──→ extract_theme_colors()
                         ├──→ extract_theme_fonts()
                         └──→ extract_layouts()
```

---

## Sources Summary

### Libraries & Tools

| Library | Version | License | Purpose |
|---------|---------|---------|---------|
| [color-thief-py](https://github.com/fengsp/color-thief-py) | latest | MIT | Dominant colour extraction via MMCQ |
| [colour-science](https://pypi.org/project/colour-science/) | 0.4.7 | BSD-3 | Delta-E 2000, 90+ colour spaces |
| [wcag-contrast-ratio](https://pypi.org/project/wcag-contrast-ratio/) | latest | MIT | WCAG AA/AAA contrast validation |
| [colorharmonies](https://pypi.org/project/colorharmonies/) | latest | MIT | Colour harmony generation (archived) |
| [python-pptx](https://python-pptx.readthedocs.io/) | 1.0.0 | MIT | PPTX theme/layout parsing |
| [Pillow](https://pillow.readthedocs.io/) | 12.1.1 | HPND | Post-generation colour correction |
| [fast-colorthief](https://github.com/bedapisl/fast-colorthief) | latest | MIT | C++ accelerated colour extraction |

### AI Image Generation APIs

| Provider | Model | Colour Control | Reference Images | Cost |
|----------|-------|---------------|-----------------|------|
| [Recraft](https://www.recraft.ai/api) | V3/V4 | `colors[]` hex array | N/A | $0.04-0.08/img |
| [Ideogram](https://developer.ideogram.ai/) | 3.0 | `color_palette` hex+weight | 3 style refs | Varies |
| [Black Forest Labs](https://bfl.ai/) | FLUX.2 Pro/Max | JSON prompt hex | 1 (Kontext) | $0.04/img |
| [Black Forest Labs](https://bfl.ai/) | FLUX Kontext | Via reference image | 1-10 images | $0.04/img |
| [OpenAI](https://platform.openai.com/) | GPT Image 1.5 | Natural language + hex | N/A | ~$0.13/img |
| [Google](https://ai.google.dev/) | Gemini 3 Pro | Reference images | Up to 14 | ~$0.13/img |

### Research Papers

- [NumColor: Precise Numeric Color Control (arXiv)](https://arxiv.org/html/2510.20586) — 4-9x improvement in colour accuracy for diffusion models
- [GenColorBench: Color Evaluation Benchmark](https://arxiv.org/html/2510.20586) — Standardized benchmark for T2I colour fidelity
