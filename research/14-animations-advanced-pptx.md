# Research 14: Animations, Transitions & Advanced PPTX Features

**Date:** 2026-03-29
**Status:** Complete
**Context:** Jack-Tar Deckhand — Claude Code skills for conference-quality PowerPoint presentations. Neither python-pptx nor PptxGenJS natively supports animations or transitions. This research explores what's possible and what workarounds exist.
**Sources:** 38 web searches, 62 sources evaluated across 10 research areas.

---

## Table of Contents

1. [OOXML Animation Specification](#1-ooxml-animation-specification)
2. [PptxGenJS Animation Support](#2-pptxgenjs-animation-support)
3. [python-pptx Animation Support](#3-python-pptx-animation-support)
4. [Aspose.Slides Evaluation](#4-asposeslides-evaluation)
5. [Progressive Build Workaround](#5-progressive-build-workaround)
6. [LibreOffice Headless Approach](#6-libreoffice-headless-approach)
7. [Video/Audio Embedding](#7-videoaudio-embedding)
8. [SmartArt Equivalents](#8-smartart-equivalents)
9. [GIF, APNG & SVG Support](#9-gif-apng--svg-support)
10. [Morph Transition](#10-morph-transition)
11. [Recommended Strategy](#11-recommended-strategy)

---

## 1. OOXML Animation Specification

### Overview

PowerPoint animations are stored in the Open XML (OOXML) format within each slide's XML file. The animation framework is loosely based on the Synchronized Multimedia Integration Language (SMIL), a W3C Recommendation for describing multimedia presentations using XML.

All animation and transition elements reside inside the slide XML file (`ppt/slides/slideN.xml`), within two top-level elements:

```xml
<p:sld>
    <p:cSld> ... </p:cSld>
    <p:clrMapOvr> ... </p:clrMapOvr>
    <p:transition> ... </p:transition>
    <p:timing> ... </p:timing>
</p:sld>
```

- **`<p:transition>`** — Controls how the slide appears (slide-level transition effects)
- **`<p:timing>`** — Controls object-level animations within the slide

### Slide Transitions (`<p:transition>`)

Transition information is specified within a `<p:transition>` element. The type of transition is specified as a child element. Three components define a transition:

1. **Type** — The visual effect (child element name)
2. **Trigger** — What starts the transition (click or automatic)
3. **Speed** — `spd` attribute: `fast`, `med`, or `slow`

#### Available Transition Types (OOXML Standard)

| XML Element | Transition Name |
|---|---|
| `<p:blinds>` | Blinds |
| `<p:checker>` | Checker |
| `<p:circle>` | Circle |
| `<p:comb>` | Comb |
| `<p:cover>` | Cover |
| `<p:cut>` | Cut |
| `<p:diamond>` | Diamond |
| `<p:dissolve>` | Dissolve |
| `<p:fade>` | Fade |
| `<p:newsflash>` | Newsflash |
| `<p:plus>` | Plus |
| `<p:pull>` | Pull |
| `<p:push>` | Push |
| `<p:random>` | Random |
| `<p:randomBar>` | Random Bar |
| `<p:split>` | Split |
| `<p:strips>` | Strips |
| `<p:wedge>` | Wedge |
| `<p:wheel>` | Wheel |
| `<p:wipe>` | Wipe |
| `<p:zoom>` | Zoom |

**Example — Fade transition:**

```xml
<p:transition spd="med">
    <p:fade />
</p:transition>
```

**Example — Push transition with direction:**

```xml
<p:transition spd="fast">
    <p:push dir="r" />
</p:transition>
```

### Object Animations (`<p:timing>`)

Object-level animations use a hierarchical timing tree:

```xml
<p:timing>
    <p:tnLst>
        <p:par>
            <p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
                <p:childTnLst>
                    <p:seq concurrent="1" nextAc="seek">
                        <p:cTn id="2" dur="indefinite" nodeType="mainSeq">
                            <p:childTnLst>
                                <!-- Animation effects go here -->
                            </p:childTnLst>
                        </p:cTn>
                    </p:seq>
                </p:childTnLst>
            </p:cTn>
        </p:par>
    </p:tnLst>
</p:timing>
```

Key elements:
- **`<p:par>`** — Parallel time container (children execute simultaneously)
- **`<p:seq>`** — Sequential time container (children execute in order)
- **`<p:cTn>`** — Common time node (timing properties)
- **`<p:childTnLst>`** — Child time node list

#### The `<p:anim>` Element

The generic animation element that can animate any attribute:

```xml
<p:anim to="1.5" calcmode="lin" valueType="num">
    <p:cBhvr override="childStyle">
        <p:cTn id="6" dur="2000" fill="hold"/>
        <p:tgtEl>
            <p:spTgt spid="3">
                <p:txEl>
                    <p:charRg st="4294967295" end="4294967295"/>
                </p:txEl>
            </p:spTgt>
        </p:tgtEl>
        <p:attrNameLst>
            <p:attrName>style.fontSize</p:attrName>
        </p:attrNameLst>
    </p:cBhvr>
</p:anim>
```

**Attributes of `<p:anim>`:**

| Attribute | Description |
|---|---|
| `by` | Relative offset value for animation |
| `calcmode` | Interpolation mode (e.g., `lin` for linear) |
| `from` | Starting value |
| `to` | Ending value |
| `valueType` | Property value type (`num`, `str`, `clr`) |

#### The `<p:animEffect>` Element

Applies image transform/filter effects:

```xml
<p:animEffect transition="in" filter="blinds(horizontal)">
    <p:cBhvr>
        <p:cTn id="7" dur="500"/>
        <p:tgtEl>
            <p:spTgt spid="4"/>
        </p:tgtEl>
    </p:cBhvr>
</p:animEffect>
```

- `transition`: `"in"` (invisible to visible), `"out"` (visible to invisible), or `"none"`
- `filter`: Effect name using `"type(subtype)"` syntax (e.g., `"fade"`, `"blinds(horizontal)"`, `"wipe(down)"`)

#### The `<p:set>` Element (Appear Animation)

Used for instant property changes like the "Appear" entrance effect:

```xml
<p:set>
    <p:cBhvr>
        <p:cTn id="5" dur="1" fill="hold">
            <p:stCondLst>
                <p:cond delay="0"/>
            </p:stCondLst>
        </p:cTn>
        <p:tgtEl>
            <p:spTgt spid="4"/>
        </p:tgtEl>
        <p:attrNameLst>
            <p:attrName>style.visibility</p:attrName>
        </p:attrNameLst>
    </p:cBhvr>
    <p:to>
        <p:strVal val="visible"/>
    </p:to>
</p:set>
```

#### Fly-In Animation with `<p:tavLst>`

```xml
<p:anim calcmode="lin" valueType="num">
    <p:cBhvr additive="base"> ... </p:cBhvr>
    <p:tavLst>
        <p:tav tm="0">
            <p:val>
                <p:strVal val="1+#ppt_h/2"/>
            </p:val>
        </p:tav>
        <p:tav tm="100000">
            <p:val>
                <p:strVal val="#ppt_y"/>
            </p:val>
        </p:tav>
    </p:tavLst>
</p:anim>
```

### Feasibility Assessment

**Writing raw transition XML: FEASIBLE.** Transition XML is simple and well-documented. A `<p:transition>` element with a single child is all that's needed.

**Writing raw animation XML: FRAGILE.** The timing tree is deeply nested with mandatory ID sequences, parallel/sequential containers, and target element references. A single misplaced ID or missing container breaks the entire animation silently. PowerPoint may strip malformed animation XML without warning.

**Post-processing injection: FEASIBLE for transitions.** Since .pptx files are ZIP archives, you can unzip, modify slide XML, and rezip. This works well for transitions. Animations are much riskier.

### Sources

- [Working with animation | Microsoft Learn](https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-animation)
- [OOXML Presentations - Transitions](http://officeopenxml.com/prSlide-transitions.php)
- [How to: Add transitions between slides | Microsoft Learn](https://learn.microsoft.com/en-us/office/open-xml/presentation/how-to-add-transitions-between-slides-in-a-presentation)
- [Anatomy of a .pptx file | SlideModel](https://slidemodel.com/anatomy-of-a-pptx-file/)
- [ISO/IEC 29500 — Office Open XML](https://www.iso.org/standard/71691.html)
- [c-rex.net OOXML timing reference](https://c-rex.net/samples/ooxml/e1/Part4/OOXML_P4_DOCX_timing_topic_ID0EYCEHB.html)

---

## 2. PptxGenJS Animation Support

### Official PptxGenJS (v4.0.1)

**Current version:** 4.0.1 (latest as of early 2026).

**Animation support: NONE.** The official PptxGenJS library does not support animations or slide transitions. The documentation explicitly lists supported features (text, tables, shapes, images, charts, media, SVGs, animated GIFs) but makes no mention of animations or transitions.

**Slide properties available:** `background`, `color`, `hidden`, `slideNumber`, `newAutoPagedSlides`. No transition or animation properties exist.

### Community Fork: @bapunhansdah/pptxgenjs

**Version:** 1.1.3 (published ~3 months ago as of March 2026)

**Animation support: YES — 44 animation types across 4 categories.**

| Category | Count | Examples |
|---|---|---|
| Entrance | 13 | appear, fade in, fly in, float in, split, wipe, shape, wheel, random bars, zoom, grow and turn, swivel, bounce |
| Emphasis | 13 | (available, types not fully enumerated) |
| Exit | 13 | (available, types not fully enumerated) |
| Path | 5 | custom motion paths |

**Animation Properties:**
- `type` — animation type
- `direction` — direction of effect
- `duration` — animation duration
- `delay` — delay before start
- `trigger` — click, with previous, after previous

**Usage:**

```javascript
import PptxGenJS from "@bapunhansdah/pptxgenjs";
const pptx = new PptxGenJS();
const slide = pptx.addSlide();

slide.addText("Hello", {
    x: 1, y: 1, w: 5, h: 1,
    animation: {
        type: "fadeIn",
        duration: 1000,
        delay: 0,
        trigger: "onClick"
    }
});

pptx.writeFile({ fileName: "demo-animation.pptx" });
```

**Interactive Playground:** [pptxgenjs-animation.vercel.app](https://pptxgenjs-animation.vercel.app/) — demonstrates animation features with real-time code generation and .pptx export.

**Risk Assessment:**
- Community fork, not maintained by the PptxGenJS core team
- Based on PptxGenJS v1.x (not v4.x) — significant version gap
- 3 months since last update — maintenance status unclear
- Should be evaluated carefully before production use

### Other Forks

- **@cf666/pptxgenjs** — Another fork on npm, features unclear
- **pptx-automizer** — Template-based approach (Node.js). Explicitly states "Animations are currently out of scope" and warns that adding/removing shapes can cause animation errors since it doesn't synchronize animation ID attributes.

### Sources

- [PptxGenJS Official](https://gitbrent.github.io/PptxGenJS/)
- [PptxGenJS GitHub](https://github.com/gitbrent/PptxGenJS)
- [@bapunhansdah/pptxgenjs on npm](https://www.npmjs.com/package/@bapunhansdah/pptxgenjs)
- [PPTX Animation Playground](https://pptxgenjs-animation.vercel.app/)
- [pptx-automizer GitHub](https://github.com/singerla/pptx-automizer)

---

## 3. python-pptx Animation Support

### Official python-pptx (v1.0.0)

**Animation support: NONE.** No public API for shape-level animations (entrance, emphasis, exit, path).

**Slide transitions: NOT in public API** but achievable via low-level XML manipulation.

**Open issues:**
- [#400 — Animation control](https://github.com/scanny/python-pptx/issues/400) (opened June 2018, still OPEN)
- [#942 — Morph transition](https://github.com/scanny/python-pptx/issues/942) (still OPEN)
- [#1106 — Shape Animations (Entrance/Exit)](https://github.com/scanny/python-pptx/issues/1106) (opened January 2026, still OPEN)

### python-pptx-ng Fork (v0.7.0)

Maintained by Martin Chrastek. A continuation of Steve Canny's original python-pptx.

**Key additions:** chart types, table cell merging/splitting, group shapes, video media insertion, OLE object embedding, gradient/patterned fills, shadow formatting, hyperlinks, notes slides, picture cropping.

**Animation support: NONE.** The changelog and documentation make no mention of animations or slide transitions.

### Direct XML Manipulation via lxml

python-pptx exposes the underlying lxml elements via `slide._element`. The xmlchemy layer provides `OxmlElement` for creating elements with namespace support.

**Adding a simple fade transition:**

```python
from pptx import Presentation
from pptx.oxml.ns import qn
from lxml import etree

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[0])

# Access the slide's XML element
sld = slide._element

# Create transition element
transition = etree.SubElement(sld, qn('p:transition'))
transition.set('spd', 'med')

# Add fade child
fade = etree.SubElement(transition, qn('p:fade'))

prs.save('output.pptx')
```

**Caveats:**
- This is unsupported — python-pptx may overwrite or strip the element
- The `<p:transition>` must appear after `<p:clrMapOvr>` and before `<p:timing>` in the XML
- Shape animations (the full `<p:timing>` tree) are far more complex and fragile
- PowerPoint silently drops malformed animation XML

### mc:AlternateContent Approach

Community members (notably MartinPacker of md2pptx) have demonstrated injecting `mc:AlternateContent` elements for modern transitions with backward-compatible fallbacks:

```xml
<mc:AlternateContent
    xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">
    <mc:Choice Requires="p14"
        xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main">
        <p:transition spd="med" p14:dur="700">
            <p:fade/>
        </p:transition>
    </mc:Choice>
    <mc:Fallback>
        <p:transition spd="med">
            <p:fade/>
        </p:transition>
    </mc:Fallback>
</mc:AlternateContent>
```

This is the approach used for morph transitions as well (see Section 10).

### Third-Party Python Libraries with Animation Support

| Library | Animation Support | Price | Notes |
|---|---|---|---|
| **Aspose.Slides for Python** | Full (animations, transitions, morph) | $999+ | See Section 4 |
| **Spire.Presentation for Python** | Full (animations, transitions, audio/video) | Commercial (free community edition available) | E-iceblue product |
| **Syncfusion Presentation** | Full (100+ animation effects) | Commercial | .NET-based with Python bindings |

### Sources

- [python-pptx documentation](https://python-pptx.readthedocs.io/)
- [python-pptx Issue #400](https://github.com/scanny/python-pptx/issues/400)
- [python-pptx Issue #942](https://github.com/scanny/python-pptx/issues/942)
- [python-pptx Issue #1106](https://github.com/scanny/python-pptx/issues/1106)
- [python-pptx-ng on PyPI](https://pypi.org/project/python-pptx-ng/)

---

## 4. Aspose.Slides Evaluation

### Feature Overview

Aspose.Slides for Python via .NET is a standalone, cross-platform library for PowerPoint processing. It does not require Microsoft Office.

| Feature | Supported |
|---|---|
| Animations (entrance, emphasis, exit, path) | Yes |
| Slide transitions (including Morph) | Yes |
| SmartArt creation and manipulation | Yes |
| Video/audio embedding | Yes |
| VBA/macro support (read, edit, create) | Yes |
| PDF export (PDF/A, PDF/UA conformance) | Yes |
| MathML support | Yes |
| Custom font fallbacks | Yes |
| Multiple slide masters | Yes |
| OLE object embedding | Yes |

### Pricing (Aspose.Slides for .NET — perpetual licenses)

| License Type | Price | Scope |
|---|---|---|
| Developer Small Business | US$999 | 1 developer, 1 deployment location |
| Developer OEM | US$2,997 | 1 developer, unlimited deployments |
| Developer SDK | US$19,980 | 1 developer, 50 commercial deployments |
| Site Small Business | US$4,995 | Up to 10 developers, 10 locations |
| Site OEM | US$13,986 | Up to 10 developers, unlimited locations |
| Metered (pay-per-use) | From US$1,999/month | Unlimited developers |

All perpetual licenses include free annual updates. Paid support starts from US$399/year.

### Aspose.Slides Cloud API

Pay-as-you-go REST API:

| Tier | Pricing |
|---|---|
| Free | 150 API calls/month |
| 151-1,150 calls | $30/month flat |
| 1,151-15,150 calls | $0.090/call |
| 15,151-30,150 calls | $0.070/call |
| 30,151-90,150 calls | $0.050/call |
| 90,150+ calls | $0.007/call |

**Cloud limitations:** The Cloud API documentation does NOT list animations, transitions, SmartArt, video/audio, or VBA among its features. It focuses on document operations (create, merge, split, convert), slide management, and content extraction.

### Verdict: Not Justified for This Project

For Jack-Tar Deckhand, the $999+ cost is not justified because:
1. **Transitions** can be achieved via XML injection (free)
2. **Progressive builds** cover ~80% of "animation" use cases (free)
3. **Media embedding** is already supported by PptxGenJS (free)
4. **SmartArt** can be built from grouped shapes (free)
5. **VBA macros** are not needed for a presentation generator

Aspose would only be justified if the project required:
- Programmatic animation of individual shapes at scale
- SmartArt with full Office fidelity
- PDF/A compliance output
- VBA macro generation

### Sources

- [Aspose.Slides Product Overview](https://docs.aspose.com/slides/python-net/product-overview/)
- [Aspose.Slides Pricing (.NET)](https://purchase.aspose.com/pricing/slides/net/)
- [Aspose Cloud Pricing](https://purchase.aspose.com/pricing/)
- [Aspose.Slides Cloud Features](https://docs.aspose.cloud/slides/aspose-slides-cloud-features/)

---

## 5. Progressive Build Workaround

### Concept

Simulate animations by generating multiple slides where each successive slide adds one more element. The presenter clicks through slides, creating the visual effect of elements "appearing."

This is the standard approach used by tools like Beamer (LaTeX), Google Slides API, and many automated presentation generators.

### Implementation Pattern

```javascript
// PptxGenJS progressive build example
const pptx = new PptxGenJS();

const bullets = [
    "First point",
    "Second point",
    "Third point",
    "Fourth point"
];

// Generate one slide per build step
for (let step = 1; step <= bullets.length; step++) {
    const slide = pptx.addSlide();

    // Set consistent background
    slide.background = { color: "FFFFFF" };

    // Add title (always visible)
    slide.addText("Our Strategy", {
        x: 0.5, y: 0.3, w: 9, h: 0.8,
        fontSize: 28, bold: true
    });

    // Add bullets up to current step
    for (let i = 0; i < step; i++) {
        slide.addText(bullets[i], {
            x: 1.0, y: 1.5 + (i * 0.6), w: 8, h: 0.5,
            fontSize: 18,
            color: i === step - 1 ? "333333" : "999999",  // Dim previous items
            bullet: true
        });
    }
}

pptx.writeFile({ fileName: "progressive-build.pptx" });
```

### File Size Implications

Each duplicated slide adds to file size, but the overhead is modest:
- Text-only slides: ~2-5 KB per slide
- Slides with background images: the image is stored once in the .pptx archive and referenced by each slide (not duplicated)
- A 4-bullet build generates 4 slides instead of 1, adding ~8-20 KB

For a typical presentation, this is negligible.

### User Experience

- **Standard practice** — Many professional presenters use manual clicking through builds
- **PDF-compatible** — Progressive builds work when exported to PDF (animations do not)
- **Remote-friendly** — Works reliably in screen sharing / video conferencing
- **Accessibility** — Screen readers can process each slide independently

### When This Is Acceptable vs. When Real Animations Are Needed

| Use Case | Progressive Build OK? | Real Animation Needed? |
|---|---|---|
| Bullet point reveals | Yes | No |
| Chart data appearing step by step | Yes | No |
| Object moving across slide | No | Yes |
| Morphing between states | No | Yes (use Morph transition) |
| Emphasis effects (pulse, spin) | No | Yes |
| Complex sequenced entrance | No | Yes |

**Recommendation:** Progressive builds should be the default approach for Jack-Tar Deckhand. They cover ~80% of "animation" use cases presenters actually need.

### Sources

- [Create a build slide | Microsoft Support](https://support.microsoft.com/en-us/office/create-a-build-slide-1776b892-4967-444c-bcaf-d4fbd0953b79)
- [PowerPoint animation tutorial | Slidor](https://www.slidor.agency/blog/powerpoint-animation-tutorial-professional-motion-effects)

---

## 6. LibreOffice Headless Approach

### Concept

1. Generate base .pptx with PptxGenJS
2. Open in LibreOffice headless mode
3. Apply transitions via UNO API
4. Save as .pptx

### LibreOffice UNO API for Transitions

LibreOffice exposes the `com.sun.star.presentation.DrawPage` service with transition properties:

- `TransitionType` — Integer specifying the transition family
- `TransitionSubtype` — Integer specifying the variant
- `Speed` — `AnimationSpeed.SLOW`, `AnimationSpeed.MEDIUM`, `AnimationSpeed.FAST`
- `Duration` — How long the slide displays before transitioning (seconds)
- `FadeEffect` — Legacy enum (e.g., `FadeEffect.FADE_FROM_LEFT`)

**Java example from SDK Guide:**

```java
Draw.setTransition(slide, FadeEffect.NONE, AnimationSpeed.FAST, Draw.AUTO_CHANGE, 1);
```

The Python-UNO bridge allows calling the same APIs from Python, though the documentation for presentation-specific APIs is sparse.

### Assessment: NOT RECOMMENDED

| Factor | Assessment |
|---|---|
| Complexity | High — requires LibreOffice installation, UNO bridge setup |
| CI/CD dependency | Adds ~500MB+ LibreOffice package to build environment |
| .pptx fidelity | LibreOffice's OOXML round-trip is imperfect — can corrupt complex slides |
| Transition quality | Limited subset compared to native PowerPoint |
| Morph support | NOT supported in LibreOffice |
| Maintenance burden | LibreOffice version updates can break UNO scripts |

**Direct XML injection (Section 1) is simpler, more reliable, and has no external dependencies.** The LibreOffice approach adds significant complexity for marginal benefit.

### Sources

- [LibreOffice SDK Overview](https://api.libreoffice.org/)
- [LibreOffice Presentation Service](https://api.libreoffice.org/docs/idl/ref/servicecom_1_1sun_1_1star_1_1presentation_1_1Presentation.html)
- [OOO Development Tools documentation](https://python-ooo-dev-tools.readthedocs.io/en/latest/odev/part1/chapter01.html)
- [LibreOffice SDK Guide: Slide Shows](https://wiki.documentfoundation.org/Documentation/SDKGuide/Slide_Shows)

---

## 7. Video/Audio Embedding

### PptxGenJS — Native Support

PptxGenJS natively supports video and audio embedding via `slide.addMedia()`.

**Video formats:** MP4, MOV, M4V, MPG
**Audio formats:** MP3, WAV
**Online video:** YouTube (via link)

**Embedded video:**

```javascript
slide.addMedia({
    type: "video",
    path: "https://example.com/media/sample.mp4",
    x: 1, y: 1, w: 8, h: 4.5
});
```

**Embedded audio (base64):**

```javascript
slide.addMedia({
    type: "audio",
    data: "audio/mp3;base64,iVtDafDrBF...",
    x: 1, y: 1, w: 3, h: 0.5
});
```

**YouTube embed:**

```javascript
slide.addMedia({
    type: "online",
    link: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    x: 1, y: 1, w: 8, h: 4.5
});
```

**Configuration options:** `x`, `y`, `w`, `h` (positioning), `path`/`data` (source), `type` (video/audio/online), `cover` (poster image), `extn` (file extension hint).

**Limitations:**
- YouTube videos only work in Microsoft 365/Office 365 (show errors on older desktop versions)
- Video codec support varies by OS (macOS handles MPG; Windows may not)

### python-pptx — Limited Support

python-pptx supports video embedding via `add_movie()`:

```python
slide.shapes.add_movie(
    movie_file, left, top, width, height,
    poster_frame_image=poster_path, mime_type='video/mp4'
)
```

Audio embedding is not directly supported in the public API.

### Speaker Narration Overlay

Both libraries can embed audio files per slide. For speaker narration:
1. Pre-record narration as separate MP3 files per slide
2. Embed each MP3 on the corresponding slide
3. Set the audio to play automatically

This works but requires manual audio production outside the presentation generator.

### Sources

- [PptxGenJS Media API](https://gitbrent.github.io/PptxGenJS/docs/api-media/)
- [PptxGenJS Media Demo](https://github.com/gitbrent/PptxGenJS/blob/master/demos/modules/demo_media.mjs)
- [python-pptx Movie analysis](https://python-pptx.readthedocs.io/en/stable/dev/analysis/shp-movie.html)

---

## 8. SmartArt Equivalents

### The Problem

SmartArt is an Office-specific feature that uses a proprietary rendering engine within PowerPoint. It is NOT part of the Open XML standard in a way that's easily programmatic. Neither PptxGenJS nor python-pptx can create SmartArt objects.

PptxGenJS explicitly lists SmartArt as NOT on its development roadmap.

### Workaround: Build from Shapes

PptxGenJS provides ~200 shape types. SmartArt-equivalent layouts can be constructed by composing basic shapes:

```javascript
// Example: Simple process flow (SmartArt equivalent)
function addProcessFlow(slide, steps, options = {}) {
    const startX = options.x || 0.5;
    const startY = options.y || 2.0;
    const boxW = options.boxWidth || 1.8;
    const boxH = options.boxHeight || 1.0;
    const gap = options.gap || 0.3;
    const arrowW = 0.4;

    steps.forEach((step, i) => {
        const x = startX + i * (boxW + gap + arrowW);

        // Add box
        slide.addShape(pptx.ShapeType.roundRect, {
            x, y: startY, w: boxW, h: boxH,
            fill: { color: "4472C4" },
            line: { color: "2F5597", width: 1 },
            rectRadius: 0.1
        });

        // Add text
        slide.addText(step, {
            x, y: startY, w: boxW, h: boxH,
            fontSize: 12, color: "FFFFFF",
            align: "center", valign: "middle"
        });

        // Add arrow (except after last)
        if (i < steps.length - 1) {
            slide.addShape(pptx.ShapeType.rightArrow, {
                x: x + boxW + 0.05,
                y: startY + boxH * 0.25,
                w: arrowW - 0.1,
                h: boxH * 0.5,
                fill: { color: "4472C4" }
            });
        }
    });
}
```

### Recommended Approach

Build a **reusable layout function library** with common SmartArt patterns:
- Process flow (linear steps with arrows)
- Hierarchy/org chart (boxes with connecting lines)
- Cycle diagram (shapes in a circle with curved arrows)
- Relationship diagram (overlapping circles / Venn)
- Matrix (2x2 or 3x3 grid)
- Pyramid (stacked trapezoids)

### How Commercial Tools Handle This

**Beautiful.ai** — Uses "Smart Slides" with automatic layout, but has significant limitations: cannot create Venn diagrams, quadrant charts, onion diagrams, flowcharts, hub-and-spoke visuals, or comparison matrices via AI. Also does NOT offer an API for programmatic deck creation.

**Aspose.Slides** — Full SmartArt creation and manipulation API. Can create SmartArt from scratch, add/remove/iterate nodes, set styles, colors, and layouts dynamically.

### Sources

- [PptxGenJS Shapes API](https://gitbrent.github.io/PptxGenJS/docs/api-shapes/)
- [PptxGenJS Issue #307 — Shape Grouping](https://github.com/gitbrent/PptxGenJS/issues/307)
- [Beautiful.ai Review 2026](https://getalai.com/blog/beautiful-ai-alternative)
- [Aspose SmartArt Guide](https://tutorials.aspose.com/slides/python-net/smart-art-diagrams/aspose-slides-python-smartart-presentation-guide/)

---

## 9. GIF, APNG & SVG Support

### Animated GIFs — WORKS

PptxGenJS supports animated GIFs via `addImage()`:

```javascript
slide.addImage({
    path: "https://example.com/animation.gif",
    x: 1, y: 1, w: 4, h: 3
});
```

**Playback behavior:**
- **Microsoft 365 / Office 365 / newest desktop:** Animated GIFs play in both editing and presentation mode
- **Older PowerPoint versions:** GIFs only animate in slide show (presentation) mode
- **PowerPoint for Web:** GIF animation support is still a requested feature

**Recommendation:** Animated GIFs are the best way to add motion to slides without real animations. Use them for:
- Loading indicators
- Micro-interactions
- Data visualization animations (pre-rendered)
- Attention-grabbing elements

### APNG (Animated PNG) — UNRELIABLE

No evidence of APNG support in PowerPoint. The search results contain no information about APNG compatibility with .pptx files. PowerPoint would likely treat an APNG as a static PNG, showing only the first frame.

**Recommendation: Do not use APNG.** Use GIF instead.

### SVG — STATIC ONLY

PptxGenJS supports SVG images:

```javascript
slide.addImage({
    path: "image.svg",
    x: 1, y: 1, w: 4, h: 3
});
```

**SVG compatibility:**
- Works in newest PowerPoint desktop and Microsoft 365/Office 365
- PowerPoint automatically generates a PNG fallback for backward compatibility with PowerPoint 2013 and earlier
- Complex/large SVGs can slow down PowerPoint

**SVG Animation: NOT SUPPORTED.** PowerPoint strips all SVG animations (CSS animations, SMIL animations, hover effects). As Microsoft confirms: "Office applications support SVG images but do not support SVG Animation."

**Workaround:** Convert SVG to individual shapes in PowerPoint, then apply PowerPoint-native animations to the shapes. This is a manual process, not automatable via PptxGenJS.

**Recommendation:** Use SVG for static vector graphics (icons, logos, diagrams). Never rely on SVG animation in .pptx files.

### Sources

- [PptxGenJS Images API](https://gitbrent.github.io/PptxGenJS/docs/api-images/)
- [Add an animated GIF to a slide | Microsoft Support](https://support.microsoft.com/en-us/office/add-an-animated-gif-to-a-slide-3a04f755-25a9-42c4-8cc1-1da4148aef01)
- [SVG file loses animation in PowerPoint | Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/5027386/svg-file-losses-its-animation-after-inserting-it-i)
- [SVG in PowerPoint | SlideModel](https://slidemodel.com/svg-in-powerpoint/)

---

## 10. Morph Transition

### What Morph Does

PowerPoint's Morph transition creates smooth animation between two slides by automatically interpolating the position, size, rotation, and opacity of objects that appear on both slides. It is the single most powerful animation feature in modern PowerPoint.

### OOXML Structure

Morph uses the `mc:AlternateContent` wrapper with a PowerPoint 2015 namespace:

**Target namespace:** `http://schemas.microsoft.com/office/powerpoint/2015/09/main`

The XML schema defines:

```xml
<xsd:element name="morph" type="CT_MorphTransition"/>
```

**Complete XML for a morph transition on a slide:**

```xml
<mc:AlternateContent
    xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">
    <mc:Choice Requires="p159"
        xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main">
        <p:transition spd="slow">
            <p159:morph option="byObject"/>
        </p:transition>
    </mc:Choice>
    <mc:Fallback>
        <p:transition spd="slow">
            <p:fade/>
        </p:transition>
    </mc:Fallback>
</mc:AlternateContent>
```

**CT_MorphTransition attributes:**
- `option` — `"byObject"` (default), `"byWord"`, or `"byChar"`

### Object Matching with `!!` Naming

Morph matches objects between consecutive slides by:
1. **Same object (same internal ID)** — Automatic when slides are duplicated
2. **`!!` naming convention** — Begin an object's name with `!!` followed by a custom name. Objects with the same `!!name` on consecutive slides are matched for morphing.

Example: An object named `!!circle1` on Slide 1 will morph into `!!circle1` on Slide 2, regardless of position, size, or rotation changes.

### Programmatic Implementation

**Achievable: YES.** The approach:

1. Create Slide 1 with objects in initial state
2. Create Slide 2 with same objects in final state (different position/size/rotation)
3. Name matching objects with `!!` prefix
4. Inject the morph transition XML (above) into Slide 2's XML as a post-processing step

**PptxGenJS post-processing pipeline:**

```javascript
const PptxGenJS = require("pptxgenjs");
const JSZip = require("jszip");
const fs = require("fs");

// 1. Generate presentation
const pptx = new PptxGenJS();
// ... add slides ...
const buffer = await pptx.write({ outputType: "arraybuffer" });

// 2. Unzip, modify, rezip
const zip = await JSZip.loadAsync(buffer);

// 3. For each slide that needs morph
const slideXml = await zip.file("ppt/slides/slide2.xml").async("string");

// 4. Inject morph transition XML before </p:sld>
const morphXml = `
<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">
    <mc:Choice Requires="p159"
        xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main">
        <p:transition spd="slow">
            <p159:morph option="byObject"/>
        </p:transition>
    </mc:Choice>
    <mc:Fallback>
        <p:transition spd="slow">
            <p:fade/>
        </p:transition>
    </mc:Fallback>
</mc:AlternateContent>`;

const modifiedXml = slideXml.replace("</p:sld>", morphXml + "</p:sld>");
zip.file("ppt/slides/slide2.xml", modifiedXml);

// 5. Save
const output = await zip.generateAsync({ type: "nodebuffer" });
fs.writeFileSync("output.pptx", output);
```

**Important caveats:**
- Morph requires PowerPoint 2019+ or Microsoft 365
- Older versions fall back to the `<mc:Fallback>` transition (fade in the example above)
- Unfilled placeholders on slides can cause morph to fail
- Object names must be set programmatically (PptxGenJS does not expose object naming directly — may require XML post-processing)

### Sources

- [[MS-PPTX]: morph | Microsoft Learn](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-pptx/68d26d78-f7f5-47ab-835d-4e6c82ff39f0)
- [Use the Morph transition | Microsoft Support](https://support.microsoft.com/en-us/office/use-the-morph-transition-in-powerpoint-8dd1c7b2-b935-44f5-a74c-741d8d9244ea)
- [Morph transition tips and tricks | Microsoft Support](https://support.microsoft.com/en-us/office/morph-transition-tips-and-tricks-bc7f48ff-f152-4ee8-9081-d3121788024f)
- [python-pptx Issue #942 — Morph](https://github.com/scanny/python-pptx/issues/942)

---

## 11. Recommended Strategy

### 4-Tier Implementation Plan

#### Tier 1: Implement Now (Free, Reliable)

| Feature | Approach | Effort |
|---|---|---|
| Progressive builds | Multiple slides with incremental content | Low |
| Animated GIFs | PptxGenJS `addImage()` with .gif files | Low |
| Video/audio embedding | PptxGenJS `addMedia()` | Low |
| SmartArt equivalents | Reusable shape-composition functions | Medium |
| SVG icons/graphics | PptxGenJS `addImage()` with .svg files | Low |

#### Tier 2: Implement Next (Free, Moderate Risk)

| Feature | Approach | Effort |
|---|---|---|
| Slide transitions (fade, push, wipe) | XML injection via JSZip post-processing | Medium |
| Morph transitions | `mc:AlternateContent` XML injection + `!!` naming | Medium-High |

#### Tier 3: Evaluate Carefully

| Feature | Approach | Risk |
|---|---|---|
| @bapunhansdah/pptxgenjs animations | Swap PptxGenJS for the fork | High — community fork, v1.x base, unclear maintenance |
| Direct OOXML animation XML | Write `<p:timing>` trees via post-processing | High — fragile, hard to debug |

#### Tier 4: Skip Unless Business Case Changes

| Feature | Why Skip |
|---|---|
| Aspose.Slides | $999+ cost not justified for current scope |
| Spire.Presentation | Similar commercial cost/complexity |
| LibreOffice headless pipeline | Adds massive dependency, imperfect .pptx fidelity |
| Raw animation XML injection | Too fragile — PowerPoint silently drops malformed XML |

### Decision Matrix

| Need | Solution | Fidelity | Cost |
|---|---|---|---|
| Bullet reveals | Progressive builds | Excellent | Free |
| Section transitions | XML-injected fade/push | Good | Free |
| Data visualization motion | Pre-rendered animated GIF | Good | Free |
| Object morphing between slides | Morph transition (XML injection) | Excellent | Free |
| Entrance animations (fade in, fly in) | @bapunhansdah fork OR skip | Variable | Free |
| Complex sequenced animations | Skip (or Aspose) | N/A | $999+ |

### Key Insight

**~80% of what presenters call "animations" are actually progressive builds.** The remaining 20% splits between transitions (achievable via XML injection) and true object animations (difficult without commercial tools or the community fork). For a presentation generator, progressive builds + transitions + animated GIFs cover the vast majority of real-world needs.
