# Draft Deck — Layout Testing Loop (Ollama Only, Zero Cost)

## Objective

Test all 5 rendering strategies using free local Ollama generation. Reuse the existing 14-slide narrative ("Presentations, Engineered"). The goal is to validate that our layout approaches work — text positioning, element composition, backdrop overlays, background zones — by iterating until the layouts are correct. Image quality doesn't matter here (it's Ollama draft quality). Layout correctness does.

**This is NOT a one-shot pipeline.** Each Ralph iteration should:
1. Check current draft state
2. Identify the next layout issue to fix or step to complete
3. Do that one thing well
4. Let the next iteration handle the next issue

## Completion Promise

Only output this when ALL quality gates pass:
```
<promise>DRAFT DECK COMPLETE</promise>
```

## State Tracking

All state lives in `./tmp/deck/draft-state.json`. Create it on first run, update it every iteration.

```json
{
  "draft_cycle": 0,
  "phase": "init",
  "slides": {},
  "qa_pass_count": 0,
  "issues": [],
  "layouts_validated": false
}
```

Phases progress: `init` → `strategy_map` → `generating` → `vision_analysis` → `assembling` → `reviewing` → `iterating` → `complete`

Each slide entry tracks:
```json
{
  "images_generated": false,
  "vision_analysed": false,
  "assembled": false,
  "reviewed": false,
  "review_status": null,
  "issues": [],
  "regen_count": 0
}
```

Read `draft-state.json` at the START of every iteration to know where you are. Update it after every meaningful action.

## Working Directory

All artifacts live in `./tmp/deck/`. Existing contracts to reuse (DO NOT MODIFY):
- `brand-profile.json` (metamirror.io)
- `style-guide.json`
- `outline.json` (14-slide Duarte Sparkline)
- `speaker-notes.json`

---

## Phase 1: Strategy Map (one-time)

If `strategy-map.json` doesn't contain all 5 strategies, write it with these assignments:

| Slide | Strategy | Variant/Layout | Image Needs |
|-------|----------|----------------|-------------|
| 1 | `full_render` | — | 1 hero image |
| 2 | `background` | `left_panel` | 1 atmospheric bg |
| 3 | `composed` | — | 1 diagram (keep existing) |
| 4 | `composed` | — | none (text only) |
| 5 | `backdrop` | `grid_2x2`, 4 elements | 1 scene image |
| 6 | `composed` | — | 1 diagram (keep existing) |
| 7 | `background` | `right_panel` | 1 atmospheric bg |
| 8 | `composed` | — | none (text only) |
| 9 | `pragmatic_composition` | `three_across`, 3 elements | 1 bg + 3 element images |
| 10 | `backdrop` | `grid_2x2`, 4 elements | 1 scene image |
| 11 | `pragmatic_composition` | `three_across`, 3 elements | 1 bg + 3 element images |
| 12 | `background` | `bottom_bar` | 1 atmospheric bg |
| 13 | `full_render` | — | 1 hero image |
| 14 | `composed` | — | none (text only) |

The full JSON for strategy-map.json:

```json
{
  "created_at": "2026-03-31T00:00:00+00:00",
  "approval_mode": "review",
  "slides": [
    {
      "slide_number": 1,
      "strategy": "full_render",
      "rationale": "Title slide — dramatic hero image, headline baked into AI image",
      "render_funnel": ["ollama"],
      "speaker_override": null
    },
    {
      "slide_number": 2,
      "strategy": "background",
      "rationale": "Content slide — atmospheric chaos background with text in left panel zone",
      "render_funnel": ["ollama"],
      "speaker_override": null,
      "backdrop_variant": "left_panel"
    },
    {
      "slide_number": 3,
      "strategy": "composed",
      "rationale": "Pipeline diagram — programmatic assembly with shapes and labels",
      "render_funnel": ["ollama"],
      "speaker_override": null
    },
    {
      "slide_number": 4,
      "strategy": "composed",
      "rationale": "Section divider — text on coloured background, no image needed",
      "render_funnel": ["ollama"],
      "speaker_override": null
    },
    {
      "slide_number": 5,
      "strategy": "backdrop",
      "rationale": "Content slide — structured scene of disconnected parts, vision-detected text positioning",
      "render_funnel": ["ollama"],
      "speaker_override": null,
      "element_layout": {
        "template": "grid_2x2",
        "elements": [
          {"id": "no_structure", "label_source": "body_points[0]", "x": 0.05, "y": 0.18, "w": 0.42, "h": 0.35},
          {"id": "no_contracts", "label_source": "body_points[1]", "x": 0.55, "y": 0.18, "w": 0.42, "h": 0.35},
          {"id": "no_quality", "label_source": "body_points[2]", "x": 0.05, "y": 0.58, "w": 0.42, "h": 0.35},
          {"id": "tangled", "label_source": "body_points[3]", "x": 0.55, "y": 0.58, "w": 0.42, "h": 0.35}
        ],
        "title_region": {"x": 0.05, "y": 0.03, "w": 0.90, "h": 0.10}
      }
    },
    {
      "slide_number": 6,
      "strategy": "composed",
      "rationale": "Architecture diagram — programmatic assembly",
      "render_funnel": ["ollama"],
      "speaker_override": null
    },
    {
      "slide_number": 7,
      "strategy": "background",
      "rationale": "Content slide — validation grid background with text in right panel zone",
      "render_funnel": ["ollama"],
      "speaker_override": null,
      "backdrop_variant": "right_panel"
    },
    {
      "slide_number": 8,
      "strategy": "composed",
      "rationale": "Section divider — text on coloured background, no image needed",
      "render_funnel": ["ollama"],
      "speaker_override": null
    },
    {
      "slide_number": 9,
      "strategy": "pragmatic_composition",
      "rationale": "Content slide — individual constraint elements placed at prescribed positions with labels",
      "render_funnel": ["ollama"],
      "speaker_override": null,
      "element_layout": {
        "template": "three_across",
        "elements": [
          {"id": "locked_output", "label_source": "body_points[0]", "x": 0.05, "y": 0.22, "w": 0.27, "h": 0.50},
          {"id": "rigid_style", "label_source": "body_points[2]", "x": 0.37, "y": 0.22, "w": 0.27, "h": 0.50},
          {"id": "passive_human", "label_source": "body_points[3]", "x": 0.69, "y": 0.22, "w": 0.27, "h": 0.50}
        ],
        "title_region": {"x": 0.05, "y": 0.03, "w": 0.90, "h": 0.12}
      }
    },
    {
      "slide_number": 10,
      "strategy": "backdrop",
      "rationale": "Content slide — AI/human dialogue scene, vision-detected text positioning",
      "render_funnel": ["ollama"],
      "speaker_override": null,
      "element_layout": {
        "template": "grid_2x2",
        "elements": [
          {"id": "narrative_arcs", "label_source": "body_points[0]", "x": 0.05, "y": 0.18, "w": 0.42, "h": 0.35},
          {"id": "palette_mood", "label_source": "body_points[1]", "x": 0.55, "y": 0.18, "w": 0.42, "h": 0.35},
          {"id": "strategy_override", "label_source": "body_points[2]", "x": 0.05, "y": 0.58, "w": 0.42, "h": 0.35},
          {"id": "human_decides", "label_source": "body_points[3]", "x": 0.55, "y": 0.58, "w": 0.42, "h": 0.35}
        ],
        "title_region": {"x": 0.05, "y": 0.03, "w": 0.90, "h": 0.10}
      }
    },
    {
      "slide_number": 11,
      "strategy": "pragmatic_composition",
      "rationale": "Content slide — three rendering strategy panels as individual elements",
      "render_funnel": ["ollama"],
      "speaker_override": null,
      "element_layout": {
        "template": "three_across",
        "elements": [
          {"id": "full_render_panel", "label_source": "body_points[0]", "x": 0.05, "y": 0.22, "w": 0.27, "h": 0.50},
          {"id": "backdrop_panel", "label_source": "body_points[1]", "x": 0.37, "y": 0.22, "w": 0.27, "h": 0.50},
          {"id": "composed_panel", "label_source": "body_points[2]", "x": 0.69, "y": 0.22, "w": 0.27, "h": 0.50}
        ],
        "title_region": {"x": 0.05, "y": 0.03, "w": 0.90, "h": 0.12}
      }
    },
    {
      "slide_number": 12,
      "strategy": "background",
      "rationale": "Content slide — progression background with text in bottom bar zone",
      "render_funnel": ["ollama"],
      "speaker_override": null,
      "backdrop_variant": "bottom_bar"
    },
    {
      "slide_number": 13,
      "strategy": "full_render",
      "rationale": "Blank visual — cinematic payoff image, no text overlay",
      "render_funnel": ["ollama"],
      "speaker_override": null
    },
    {
      "slide_number": 14,
      "strategy": "composed",
      "rationale": "Closing slide — brand text on primary background, no image needed",
      "render_funnel": ["ollama"],
      "speaker_override": null
    }
  ]
}
```

Validate:
```bash
python3 -c "
from src.slide_prompt_composer import load_strategy_map
sm = load_strategy_map('./tmp/deck')
strategies = set(e['strategy'] for e in sm['slides'])
print(f'Strategies: {strategies}')
assert len(strategies & {'full_render','background','backdrop','pragmatic_composition','composed'}) == 5
print('All 5 strategies present')
"
```

Update phase to `strategy_map` in draft-state.json.

---

## Phase 2: Image Generation

Use model `x/z-image-turbo:fp8`, resolution 1024x576 (16:9).

```bash
python3 src/generate_image.py --prompt "PROMPT" --model "x/z-image-turbo:fp8" --output "PATH" --width 1024 --height 576 --timeout 120
```

**First, clean up old images** that don't match the new strategy naming:
```bash
# Remove old hero images for slides that are now background/backdrop/pragmatic
rm -f ./tmp/deck/images/slide-02-hero.png  # now background
rm -f ./tmp/deck/images/slide-05-hero.png  # now backdrop
rm -f ./tmp/deck/images/slide-07-hero.png  # now background
rm -f ./tmp/deck/images/slide-09-hero.png  # now pragmatic
rm -f ./tmp/deck/images/slide-10-hero.png  # now backdrop
rm -f ./tmp/deck/images/slide-11-hero.png  # now pragmatic
rm -f ./tmp/deck/images/slide-12-hero.png  # now background
# Keep logo.png, slide-03-diagram.png, slide-06-diagram.png
```

Generate each image. Skip files that already exist at the correct path. For each image, update the slide's `images_generated` flag in draft-state.json.

### Image Generation Table

| Slide | Strategy | File Path | Prompt |
|-------|----------|-----------|--------|
| 1 | full_render | `images/slide-01-hero.png` | Abstract geometric composition of interlocking teal crystalline forms emerging from dark depth. Deep teal (#006B5E), reflection mint (#5CDBC0), dark surface (#0E1513). Bold cinematic composition with strong depth and light. Text "Presentations, Engineered" in large white font. Professional, striking, engineered precision. |
| 2 | background | `images/slide-02-bg.png` | Abstract atmospheric backdrop of scattered, misaligned geometric fragments in muted silver and secondary teal on dark surface. Conveys disorder and frustration. Shapes disconnected, overlapping awkwardly. Visual chaos. NO TEXT in the image. Deep teal (#006B5E), silver (#9DA3A0), secondary teal (#4B635B), dark surface (#0E1513). |
| 5 | backdrop | `images/slide-05-scene.png` | Abstract scene of disconnected mechanical parts, gears, connectors, structural elements that do not fit together. Four distinct groups of parts arranged in a 2x2 grid pattern with clear separation between groups. Muted palette: silver (#9DA3A0), secondary teal (#4B635B) on dark background (#0E1513). Parts are individually well-made but unconnected. NO TEXT. |
| 7 | background | `images/slide-07-bg.png` | Abstract backdrop of a precise grid of geometric check-marks and validation symbols in structured rows. Deep teal (#006B5E) on light surface (#F5FBF7) with selective mint (#5CDBC0) highlights. Systematic coverage and engineering discipline. Clean, methodical, confident. NO TEXT. |
| 9 bg | pragmatic | `images/slide-09-bg.png` | Dark atmospheric abstract background texture. Oppressive angular dark geometry suggesting confinement. Dark tones (#0E1513, #4B635B). Moody, restrictive, claustrophobic. NO TEXT, no distinct objects, just atmospheric texture. |
| 9 e1 | pragmatic | `images/slide-09-elem-locked_output.png` | Single abstract geometric icon of a locked padlock or sealed box, single fixed output with no alternatives. Deep teal (#006B5E) and dark surface (#0E1513). Clean flat illustration, isolated on very dark background. NO TEXT. |
| 9 e2 | pragmatic | `images/slide-09-elem-rigid_style.png` | Single abstract geometric icon of rigid inflexible interlocking bars or fixed template frame, style baked in and not customisable. Silver (#9DA3A0) and dark teal (#4B635B). Clean flat illustration, isolated on very dark background. NO TEXT. |
| 9 e3 | pragmatic | `images/slide-09-elem-passive_human.png` | Single abstract geometric icon of a small figure behind glass or one-way mirror, passive reviewer who cannot create. Muted silver (#9DA3A0) and teal (#006B5E). Clean flat illustration, isolated on very dark background. NO TEXT. |
| 10 | backdrop | `images/slide-10-scene.png` | Abstract scene showing two geometric forms in dialogue. Left side: angular precise crystalline shapes representing AI. Right side: flowing organic curves representing human creativity. Meeting in centre, creating something new. Brand teal (#006B5E) for AI, reflection mint (#5CDBC0) for human. Four distinct visual regions in 2x2 pattern. NO TEXT. |
| 11 bg | pragmatic | `images/slide-11-bg.png` | Clean neutral dark background with subtle geometric grid pattern. Dark surface (#0E1513) with very faint teal (#006B5E) grid lines. Minimal, technical, professional. NO TEXT, no distinct objects. |
| 11 e1 | pragmatic | `images/slide-11-elem-full_render_panel.png` | Preview of a presentation slide rendered as a single artistic AI-generated image. Dramatic, bold, cinematic. Complete visual scene filling the entire frame. Teal (#006B5E) and mint (#5CDBC0). Clean flat illustration. NO TEXT. |
| 11 e2 | pragmatic | `images/slide-11-elem-backdrop_panel.png` | Preview of a presentation slide with an AI-generated background image and a semi-transparent text overlay panel on one side. Image plus editable text zone. Teal (#006B5E) and mint (#5CDBC0). Clean flat illustration. NO TEXT. |
| 11 e3 | pragmatic | `images/slide-11-elem-composed_panel.png` | Preview of a presentation slide with structured layout: shapes, boxes, text areas, small chart. Standard professional deck layout. Precise programmatic assembly. Teal (#006B5E) and mint (#5CDBC0). Clean flat illustration. NO TEXT. |
| 12 | background | `images/slide-12-bg.png` | Abstract backdrop showing three-stage progression flowing left to right. Left: rough sketchy geometric form in muted grey. Centre: refined mid-stage in brand teal (#006B5E). Right: polished crystalline form in vivid mint (#5CDBC0). Clear directional flow, draft to production. NO TEXT. |
| 13 | full_render | `images/slide-13-hero.png` | Full-bleed cinematic image: scattered chaotic geometric fragments transformed into a single magnificent crystalline structure. Precise, unified, radiant. Deep teal (#006B5E) core, reflection mint (#5CDBC0) edges catching light, primary container (#7AF8DB) highlights. Dark background (#0E1513). Order from complexity. Dramatic, complete. No text. |

Diagrams (keep existing if present, use `x/flux2-klein:4b` at 1024x768 if missing):
- `images/slide-03-diagram.png` — pipeline flow: Brief → Brand → Style → Narrative → Images → Assembly → QA → Deck
- `images/slide-06-diagram.png` — architecture: Content, Design, Image, Assembly & QA services with Deck Conductor

Update phase to `generating` in draft-state.json. Once all images exist, move to `vision_analysis`.

---

## Phase 3: Vision Analysis (Backdrop Slides)

**This is critical.** For backdrop slides (5, 10), the vision-analyst agent must analyse the scene image to detect where visual elements are positioned. This produces `detected_positions` that the assembler uses for text placement instead of the prescribed fallbacks.

For each backdrop slide:

1. **Read the scene image** using the Read tool (it supports images)
2. **Analyse element positions** — look at the image and identify where the visual element groups are
3. **Write detected_positions** into the image manifest entry for that scene image

The detected_positions array goes on the scene image's manifest entry:
```json
{
  "slide_number": 5,
  "file_path": "./tmp/deck/images/slide-05-scene.png",
  "detected_positions": [
    {"element_id": "no_structure", "x": 0.05, "y": 0.10, "w": 0.40, "h": 0.35, "confidence": 0.85},
    {"element_id": "no_contracts", "x": 0.55, "y": 0.10, "w": 0.40, "h": 0.35, "confidence": 0.82},
    {"element_id": "no_quality", "x": 0.05, "y": 0.55, "w": 0.40, "h": 0.35, "confidence": 0.80},
    {"element_id": "tangled", "x": 0.55, "y": 0.55, "w": 0.40, "h": 0.35, "confidence": 0.78}
  ]
}
```

**Quality gate:** If any element confidence is below 0.5, the scene image is too ambiguous. Regenerate it with an adjusted prompt that makes the element groups more distinct, then re-analyse.

### Slide 5 — "Pile of Parts"
- Look for 4 distinct groups of disconnected parts in the image
- Map each group to: no_structure (top-left), no_contracts (top-right), no_quality (bottom-left), tangled (bottom-right)
- element_ids MUST match the strategy map element ids exactly

### Slide 10 — "Skills Propose. You Decide."
- Look for the AI (angular/crystalline) and human (organic/flowing) forms
- Map visual regions to: narrative_arcs (top-left), palette_mood (top-right), strategy_override (bottom-left), human_decides (bottom-right)
- element_ids MUST match the strategy map element ids exactly

Update phase to `vision_analysis` in draft-state.json. Mark each slide's `vision_analysed: true`.

---

## Phase 4: Build Image Manifest

Write `./tmp/deck/image-manifest.json` with ALL images. Use this Python script:

```python
import json, os, hashlib
from datetime import datetime, timezone
from PIL import Image

DECK_DIR = './tmp/deck'

def image_entry(slide_number, file_path, alt_text, element_id=None, placement_zone=None, detected_positions=None):
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        print(f'WARNING: missing {file_path}')
        return None
    with open(abs_path, 'rb') as f:
        content_hash = hashlib.sha256(f.read()).hexdigest()
    img = Image.open(abs_path)
    w, h = img.size
    entry = {
        'slide_number': slide_number,
        'file_path': file_path,
        'status': 'generated',
        'content_hash': content_hash,
        'dimensions': {'width': w, 'height': h},
        'alt_text': alt_text,
        'image_id': os.path.splitext(os.path.basename(file_path))[0],
        'model_used': 'x/z-image-turbo:fp8',
    }
    if element_id:
        entry['element_id'] = element_id
    if placement_zone:
        entry['placement_zone'] = placement_zone
    if detected_positions:
        entry['detected_positions'] = detected_positions
    return entry

images = []

# full_render
images.append(image_entry(1, './tmp/deck/images/slide-01-hero.png', 'Presentations, Engineered'))
images.append(image_entry(13, './tmp/deck/images/slide-13-hero.png', 'This Deck Was Built by the Pipeline'))

# background
images.append(image_entry(2, './tmp/deck/images/slide-02-bg.png', 'Every Deck Starts With a Blank Slide and a Sigh'))
images.append(image_entry(7, './tmp/deck/images/slide-07-bg.png', 'Every Skill Has a Contract. Every Contract Has Tests.'))
images.append(image_entry(12, './tmp/deck/images/slide-12-bg.png', 'Draft Fast. Produce Once.'))

# backdrop — INCLUDE detected_positions from Phase 3
# READ detected positions from draft-state.json and inject here
images.append(image_entry(5, './tmp/deck/images/slide-05-scene.png',
    'Features Without Architecture Is Just a Pile of Parts',
    detected_positions=SLIDE_5_DETECTED))  # Replace with actual detected positions
images.append(image_entry(10, './tmp/deck/images/slide-10-scene.png',
    'Skills Propose. You Decide.',
    detected_positions=SLIDE_10_DETECTED))  # Replace with actual detected positions

# pragmatic slide 9
images.append(image_entry(9, './tmp/deck/images/slide-09-bg.png', 'Slide 9 background', placement_zone='background'))
images.append(image_entry(9, './tmp/deck/images/slide-09-elem-locked_output.png', 'Locked output', element_id='locked_output'))
images.append(image_entry(9, './tmp/deck/images/slide-09-elem-rigid_style.png', 'Rigid style', element_id='rigid_style'))
images.append(image_entry(9, './tmp/deck/images/slide-09-elem-passive_human.png', 'Passive human', element_id='passive_human'))

# pragmatic slide 11
images.append(image_entry(11, './tmp/deck/images/slide-11-bg.png', 'Slide 11 background', placement_zone='background'))
images.append(image_entry(11, './tmp/deck/images/slide-11-elem-full_render_panel.png', 'Full render', element_id='full_render_panel'))
images.append(image_entry(11, './tmp/deck/images/slide-11-elem-backdrop_panel.png', 'Backdrop render', element_id='backdrop_panel'))
images.append(image_entry(11, './tmp/deck/images/slide-11-elem-composed_panel.png', 'Composed', element_id='composed_panel'))

# composed diagrams
images.append(image_entry(3, './tmp/deck/images/slide-03-diagram.png', 'Brief In. Polished Deck Out.'))
images.append(image_entry(6, './tmp/deck/images/slide-06-diagram.png', 'Four Services. Four Personas. One Pipeline.'))

images = [img for img in images if img is not None]

manifest = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'image_backend': 'ollama-draft',
    'images': images,
    'summary': {
        'total_images': len(images),
        'generated_count': len(images),
        'cached_count': 0,
        'placeholder_count': 0,
        'failed_count': 0,
    }
}

with open(os.path.join(DECK_DIR, 'image-manifest.json'), 'w') as f:
    json.dump(manifest, f, indent=2)
    f.write('\n')
print(f'Wrote image-manifest.json with {len(images)} images')
```

**Important:** The `SLIDE_5_DETECTED` and `SLIDE_10_DETECTED` placeholders must be replaced with the actual detected_positions arrays from Phase 3. Read them from draft-state.json or compute them inline.

---

## Phase 5: Assemble & Review Cycle

This is the core iteration loop. Repeat until all slides pass review.

### 5a. Assemble
```bash
node src/assembler/build_deck.js --deck-dir ./tmp/deck
```

### 5b. Review Each Slide

After assembly, review the deck by reading the .pptx output and checking each strategy type:

#### Background slides (2, 7, 12) — check:
- [ ] Text zone is positioned correctly for the variant (left_panel, right_panel, bottom_bar)
- [ ] Semi-transparent overlay is present behind text
- [ ] Text is readable against the background image
- [ ] Background image fills the full slide (no white gaps)

#### Backdrop slides (5, 10) — check:
- [ ] Scene image fills the full slide
- [ ] Text labels are positioned at detected element locations (not overlapping each other)
- [ ] Labels don't extend off-slide (x+w <= 1.0, y+h <= 1.0)
- [ ] Backing pills are visible behind text
- [ ] If labels overlap or are off-slide, adjust detected_positions in the manifest and re-assemble

#### Pragmatic composition slides (9, 11) — check:
- [ ] Background image fills the full slide
- [ ] Element images appear at prescribed positions (three_across layout)
- [ ] Text labels appear below each element (or above if element is in bottom third)
- [ ] Elements don't overlap each other
- [ ] Headline appears in the title region

#### Full render slides (1, 13) — check:
- [ ] Image fills the full slide (correct dimensions, no white gaps)
- [ ] For slide 1: headline text is part of the image (full_render bakes text in)
- [ ] For slide 13: image covers full slide area (quality doesn't matter for draft)

#### Composed slides (3, 4, 6, 8, 14) — check:
- [ ] Text renders correctly
- [ ] Diagrams (3, 6) display their images
- [ ] Section dividers (4, 8) have correct background colour (#7AF8DB)
- [ ] Closing slide (14) has correct background colour (#006B5E)

### 5c. Fix Issues

For each issue found during review:

**Bad text positioning (backdrop):**
→ Adjust the `detected_positions` in image-manifest.json
→ Re-assemble (no need to regenerate images)

**Text not readable over background:**
→ Check that the overlay transparency is appropriate
→ If the background image is too busy/bright, regenerate with adjusted prompt emphasising "dark", "muted", "atmospheric"
→ Re-build manifest, re-assemble

**Elements overlapping (pragmatic):**
→ Adjust element positions in strategy-map.json (the x, y, w, h values)
→ Re-assemble

**Image quality poor (layout-affecting only):**
→ Don't chase image quality — this is Ollama draft, it will look rough
→ Only regenerate if the image is so bad it breaks layout testing (e.g., blank image, wrong aspect ratio, no discernible elements for backdrop detection)
→ Increment `regen_count` in draft-state.json (max 3 per image)

**Missing image file:**
→ Regenerate it
→ Re-build manifest

### 5d. Track Progress

After each review, update draft-state.json:
```json
{
  "draft_cycle": 2,
  "phase": "iterating",
  "slides": {
    "1": {"images_generated": true, "reviewed": true, "review_status": "pass"},
    "5": {"images_generated": true, "vision_analysed": true, "reviewed": true, "review_status": "needs_adjustment", "issues": ["label overlap on no_quality and tangled"]},
    ...
  }
}
```

Increment `draft_cycle` each time you go through the full assemble-review loop.

---

## Phase 6: QA

Once all slides pass visual review, run automated QA:

```bash
python3 -m src.qa.run_qa --deck-dir ./tmp/deck --pptx-path ./tmp/deck/output/presentation.pptx
```

Read `./tmp/deck/qa-report.json` and check the verdict.

**If verdict is `fail`:**
- Read the findings
- Fix critical/error-level issues (re-generate images, adjust positions, re-assemble)
- Run QA again
- Max 2 QA correction cycles

**If verdict is `pass` or `pass_with_warnings`:**
- Warnings are acceptable for a draft
- Record qa_pass_count in draft-state.json

**Key QA checks for new strategies:**
- AP-27 (element_layout validation): elements within bounds, count <= 5, valid label_source refs
- AP-28 (vision confidence): detected_positions confidence >= 0.7

---

## Phase 7: Completion

Only when ALL of these are true:
1. All 17 images generated successfully
2. Vision analysis done for backdrop slides (5, 10) with confidence >= 0.5
3. Deck assembled without errors
4. All slide LAYOUTS reviewed and validated:
   - Background zone text positioning correct for all 3 variants (left_panel, right_panel, bottom_bar)
   - Backdrop text labels placed at vision-detected positions without overlap or off-slide
   - Pragmatic element images at correct positions with labels adjacent
   - Full render images filling slides correctly
   - Composed slides rendering text/diagrams properly
5. QA verdict is pass or pass_with_warnings
6. draft_cycle >= 1 (at least one full review cycle completed)

Update draft-state.json:
```json
{
  "phase": "complete",
  "layouts_validated": true
}
```

Print a summary:
```
LAYOUT TESTING SUMMARY
======================
Slides: 14
Strategies tested: full_render(2), background(3), backdrop(2), pragmatic_composition(2), composed(5)
Images: 17 generated (Ollama x/z-image-turbo:fp8, zero cost)
Draft cycles: N
QA verdict: pass/pass_with_warnings
Layout issues fixed: N
Output: ./tmp/deck/output/presentation.pptx

All 5 rendering strategies validated. Layouts correct.
```

Then output:
```
<promise>DRAFT DECK COMPLETE</promise>
```

---

## Important Rules

1. **Ollama only** — do NOT use any cloud providers. Zero cost. This is local machine only.
2. **Layout correctness is the goal, not image quality** — Ollama images will look rough. That's fine. We're testing whether text lands in the right zones, elements don't overlap, overlays are positioned correctly, and all 5 strategies produce valid slide layouts.
3. **Do not modify** `outline.json`, `style-guide.json`, `brand-profile.json`, or `speaker-notes.json`
4. **Image generation takes time** — ~40-60 seconds per image. Use `--timeout 120`
5. **Max 3 regenerations per image** — only regenerate for layout-breaking issues (blank, wrong ratio, undetectable elements), not for aesthetics
6. **Max 2 QA correction cycles** — accept warnings on a draft
7. **Keep logo.png** — `./tmp/deck/images/logo.png` must not be deleted
8. **One thing per iteration** — don't try to do everything in one pass. Generate images in one iteration, analyse in the next, assemble in the next, review in the next. Ralph gives you unlimited iterations — use them.
9. **Always read draft-state.json first** — know where you are before acting
10. **Vision analysis is NOT optional** for backdrop slides — the whole point is vision-detected positioning, not just falling back to prescribed positions. Iterate the positions until they're right.
11. **Iterate positions aggressively** — if a backdrop label is off-position or a pragmatic element overlaps, adjust coordinates and re-assemble. This is free. Keep going until the layout is correct. This is what the drafting loop is for.
