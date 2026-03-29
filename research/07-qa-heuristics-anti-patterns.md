# Conference Presentation QA Heuristics & Anti-Patterns

> Research for the Jack-Tar Deckhand `deck-qa` skill — a codified, machine-checkable rulebook for automated quality assurance of conference-quality PowerPoint presentations.

---

## Table of Contents

1. [Top 25 Presentation Anti-Patterns](#1-top-25-presentation-anti-patterns)
2. [WCAG Contrast at Projection Distance](#2-wcag-contrast-at-projection-distance)
3. [Professional AV Specifications](#3-professional-av-specifications)
4. [Image Quality Thresholds](#4-image-quality-thresholds)
5. [Automated Visual Regression Testing](#5-automated-visual-regression-testing)
6. [QA Pipeline Design](#6-qa-pipeline-design)
7. [Sources](#7-sources)

---

## 1. Top 25 Presentation Anti-Patterns

Each anti-pattern includes: ID, name, description, why it matters, a concrete detection algorithm, severity level, and a fix suggestion.

### AP-01: Wall of Text

**Description:** A single text box or slide contains an excessive number of words, overwhelming the audience with dense paragraphs.

**Why it's bad:** The human eye reads 150-300 words per minute. A 40-word slide takes ~15 seconds to read. Audiences should grasp the point in 3 seconds or less. Text overload reduces attention span and fails to inspire action ([presentationmagazine.com](https://www.presentationmagazine.com/how-many-words-should-i-have-on-each-slide-18345.htm), [storytellingwithdata.com](https://www.storytellingwithdata.com/blog/how-many-words-is-too-many)).

**Detection Algorithm (python-pptx):**
```python
def check_wall_of_text(slide, max_words_per_textbox=40, max_words_per_slide=75):
    issues = []
    slide_word_count = 0
    for shape in slide.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text.strip()
            word_count = len(text.split())
            slide_word_count += word_count
            if word_count > max_words_per_textbox:
                issues.append({
                    'rule': 'AP-01',
                    'severity': 'error',
                    'message': f'Text box has {word_count} words (max {max_words_per_textbox})',
                    'shape_name': shape.name,
                })
    if slide_word_count > max_words_per_slide:
        issues.append({
            'rule': 'AP-01',
            'severity': 'error',
            'message': f'Slide has {slide_word_count} total words (max {max_words_per_slide})',
        })
    return issues
```

**Severity:** Error

**Fix:** Break content across multiple slides. Apply the 6x6 rule: no more than 6 lines, no more than 6 words per line. Target 30 words or fewer per slide ([shapechef.com](https://www.shapechef.com/blog/how-many-words-per-slide), [microsoft.com](https://www.microsoft.com/en-us/microsoft-365-life-hacks/presentations/10-20-30-rule-of-powerpoint)).

---

### AP-02: Font Size Below Projection Minimum

**Description:** Text uses a font size too small to be legible when projected in a conference venue.

**Why it's bad:** Anything smaller than 18pt becomes difficult to read in a room, especially on projectors. For large venues (conferences/lecture halls), 30-34pt is the minimum for visibility from back rows. The distance rule: 1 inch of on-screen text height per 15 feet of viewing distance ([brightcarbon.com](https://www.brightcarbon.com/blog/presentation-font-size/), [beautiful.ai](https://www.beautiful.ai/blog/what-font-size-is-best-for-presentations)).

**Detection Algorithm (python-pptx):**
```python
from pptx.util import Pt

def check_font_size(slide, min_body_pt=18, min_title_pt=24):
    issues = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    font_size = run.font.size
                    if font_size is not None:
                        size_pt = font_size.pt
                        # Check if this is a title placeholder
                        is_title = hasattr(shape, 'placeholder_format') and \
                                   shape.placeholder_format is not None and \
                                   shape.placeholder_format.idx in (0, 1)  # title/subtitle
                        threshold = min_title_pt if is_title else min_body_pt
                        if size_pt < threshold:
                            issues.append({
                                'rule': 'AP-02',
                                'severity': 'error',
                                'message': f'Font size {size_pt}pt below minimum {threshold}pt',
                                'shape_name': shape.name,
                                'text_preview': run.text[:50],
                            })
    return issues
```

**Severity:** Error

**Fix:** Increase font sizes. Recommended minimums for conference presentations: titles 28pt+, body text 24pt+, labels/callouts 18pt+ ([autoppt.com](https://autoppt.com/blog/powerpoint-minimum-font-size-best-practices/)).

---

### AP-03: Too Many Font Families

**Description:** The deck uses more than 2 font families, creating visual chaos.

**Why it's bad:** Font overuse diminishes professional credibility. Two font families is the standard professional recommendation, with three as an absolute upper limit ([slidor.agency](https://www.slidor.agency/blog/best-fonts-powerpoint-presentations-designers-guide), [learn.aippt.com](https://learn.aippt.com/best-practices-for-powerpoint-typography-and-text-readability/)).

**Detection Algorithm (python-pptx):**
```python
def check_font_families(presentation, max_families=2):
    font_families = set()
    for slide in presentation.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        if run.font.name:
                            font_families.add(run.font.name)
    issues = []
    if len(font_families) > max_families:
        issues.append({
            'rule': 'AP-03',
            'severity': 'warning',
            'message': f'Deck uses {len(font_families)} font families (max {max_families}): {", ".join(sorted(font_families))}',
        })
    return issues
```

**Severity:** Warning

**Fix:** Limit to 2 font families. Use one for headings, one for body text. Weight variation within a single family (bold, regular, light) creates hierarchy without adding typefaces ([presentationcorner.com](https://presentationcorner.com/en/articles/best-fonts-for-presentations.html)).

---

### AP-04: Inconsistent Bullet Styles

**Description:** Different slides or text boxes use different bullet characters, sizes, or indentation levels inconsistently.

**Why it's bad:** Inconsistency signals a lack of polish and makes the deck look assembled from different sources rather than professionally designed.

**Detection Algorithm (python-pptx):**
```python
def check_bullet_consistency(presentation):
    bullet_styles = []  # Collect (bullet_char, indent_level, font_size) tuples
    for slide in presentation.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    pPr = para._pPr  # Access paragraph properties XML
                    if pPr is not None:
                        buChar = pPr.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}buChar')
                        if buChar is not None:
                            bullet_styles.append({
                                'char': buChar.get('char'),
                                'level': para.level,
                                'slide': slide.slide_id,
                            })
    # Check for inconsistency: same level should use same bullet char
    level_chars = {}
    issues = []
    for style in bullet_styles:
        level = style['level']
        char = style['char']
        if level not in level_chars:
            level_chars[level] = char
        elif level_chars[level] != char:
            issues.append({
                'rule': 'AP-04',
                'severity': 'warning',
                'message': f'Inconsistent bullet at level {level}: "{char}" vs "{level_chars[level]}"',
            })
    return issues
```

**Severity:** Warning

**Fix:** Standardise bullet characters per indentation level across the entire deck via the slide master.

---

### AP-05: Orphan/Widow Lines

**Description:** A single word or very short line sits alone at the end of a paragraph, or a single line of a paragraph is isolated at the start of a new text box continuation.

**Why it's bad:** Orphans and widows disrupt the reader's eye and instantly reduce the professionalism of any text block ([fontfabric.com](https://www.fontfabric.com/blog/orphan-typography/), [practicaltypography.com](https://practicaltypography.com/widow-and-orphan-control.html)).

**Detection Algorithm (python-pptx):**
```python
def check_orphan_widow(slide, min_last_line_chars=15):
    issues = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                lines = text.split('\n')
                if len(lines) > 1:
                    last_line = lines[-1].strip()
                    if len(last_line) < min_last_line_chars and len(last_line.split()) <= 2:
                        issues.append({
                            'rule': 'AP-05',
                            'severity': 'info',
                            'message': f'Possible widow: last line "{last_line}" is very short',
                            'shape_name': shape.name,
                        })
    return issues
```

**Severity:** Info

**Fix:** Reword text to eliminate short trailing lines. Use non-breaking spaces between the last few words to keep them together.

---

### AP-06: Elements Outside Safe Margins

**Description:** Text, logos, or other critical elements are positioned within the outer 10% of the slide, risking being cut off by projector overscan.

**Why it's bad:** Cinema projectors and many conference setups crop the edges of the image. The Title Safe area (inner 80%) must contain all critical text; the Action Safe area (inner 90%) should contain all meaningful content ([cinebox.co](https://www.cinebox.co/help/safeArea), [Wikipedia: Safe area](https://en.wikipedia.org/wiki/Safe_area_(television))).

**Detection Algorithm (python-pptx):**
```python
from pptx.util import Inches, Emu

def check_safe_margins(slide, presentation, margin_pct=0.05):
    """Check that elements with text are within the action-safe 5% margin."""
    slide_width = presentation.slide_width
    slide_height = presentation.slide_height
    margin_left = int(slide_width * margin_pct)
    margin_top = int(slide_height * margin_pct)
    margin_right = slide_width - margin_left
    margin_bottom = slide_height - margin_top

    issues = []
    for shape in slide.shapes:
        if not shape.has_text_frame or not shape.text_frame.text.strip():
            continue
        if (shape.left < margin_left or
            shape.top < margin_top or
            shape.left + shape.width > margin_right or
            shape.top + shape.height > margin_bottom):
            issues.append({
                'rule': 'AP-06',
                'severity': 'warning',
                'message': f'Element "{shape.name}" extends outside {margin_pct*100:.0f}% safe margin',
                'position': {
                    'left': shape.left, 'top': shape.top,
                    'width': shape.width, 'height': shape.height,
                },
            })
    return issues
```

**Severity:** Warning

**Fix:** Move elements inside the 5% action-safe margin (10% for critical text/titles). Full-bleed images can extend to edges, but text and logos must not.

---

### AP-07: Low Contrast Text-on-Background

**Description:** Text colour does not have sufficient contrast against its background, making it illegible especially when projected.

**Why it's bad:** WCAG AA requires 4.5:1 for normal text and 3:1 for large text. For projection, an even stricter 7:1 ratio is recommended because projectors wash out colours by 20-30% and ambient light further reduces contrast ([W3C WCAG 1.4.3](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html), [support.microsoft.com](https://support.microsoft.com/en-us/office/combining-colors-in-powerpoint-mistakes-to-avoid-555e1689-85a7-4b2e-aa89-db5270528852)).

**Detection Algorithm (python-pptx):**
```python
def relative_luminance(r, g, b):
    """Calculate relative luminance per WCAG 2.0."""
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

def contrast_ratio(rgb1, rgb2):
    """Calculate WCAG contrast ratio between two RGB tuples."""
    l1 = relative_luminance(*rgb1)
    l2 = relative_luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def check_contrast(slide, min_ratio=7.0):
    """Check text-to-background contrast. Uses 7:1 for projection safety."""
    issues = []
    # Get slide background colour (simplified — may need XML parsing for gradients)
    bg_color = (255, 255, 255)  # Default white
    bg = slide.background
    if bg.fill.type is not None:
        try:
            bg_rgb = bg.fill.fore_color.rgb
            bg_color = (bg_rgb[0], bg_rgb[1], bg_rgb[2])
        except Exception:
            pass

    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    if run.font.color and run.font.color.rgb:
                        fg = run.font.color.rgb
                        fg_color = (fg[0], fg[1], fg[2])
                        ratio = contrast_ratio(fg_color, bg_color)
                        if ratio < min_ratio:
                            issues.append({
                                'rule': 'AP-07',
                                'severity': 'error',
                                'message': f'Contrast ratio {ratio:.1f}:1 below {min_ratio}:1',
                                'fg': f'#{fg}', 'bg': f'rgb{bg_color}',
                                'text_preview': run.text[:30],
                            })
    return issues
```

**Severity:** Error

**Fix:** Use high-contrast combinations: white/light beige on dark background, or black/very dark on light background. Avoid: red on black, green on anything, light grey on white. Target 7:1+ ratio for conference presentations ([edgeforscholars.vumc.org](https://edgeforscholars.vumc.org/optimizing-colors-for-projected-presentations/)).

---

### AP-08: Clashing Colours

**Description:** The slide uses colour combinations that create visual discomfort or vibrate when viewed together.

**Why it's bad:** Red-green combinations appear to "vibrate" on screen, cause headaches, and are invisible to the ~8% of men with colour blindness. Complementary colours at full saturation (e.g. pure red and pure cyan) create harsh visual effects ([support.microsoft.com](https://support.microsoft.com/en-us/office/combining-colors-in-powerpoint-mistakes-to-avoid-555e1689-85a7-4b2e-aa89-db5270528852)).

**Detection Algorithm:**
```python
import colorsys

def rgb_to_hsv(r, g, b):
    return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

def check_clashing_colours(colours_used):
    """Check for colour pairs that clash (complementary at high saturation)."""
    issues = []
    colour_list = list(colours_used)
    for i in range(len(colour_list)):
        for j in range(i + 1, len(colour_list)):
            h1, s1, v1 = rgb_to_hsv(*colour_list[i])
            h2, s2, v2 = rgb_to_hsv(*colour_list[j])
            hue_diff = abs(h1 - h2)
            if hue_diff > 0.5:
                hue_diff = 1.0 - hue_diff
            # Complementary colours (hue diff ~0.5) at high saturation
            if 0.4 < hue_diff < 0.6 and s1 > 0.7 and s2 > 0.7:
                issues.append({
                    'rule': 'AP-08',
                    'severity': 'warning',
                    'message': f'Potentially clashing complementary colours at high saturation',
                    'colours': [colour_list[i], colour_list[j]],
                })
            # Red-green specifically
            is_red = (0.95 < h1 or h1 < 0.05) and s1 > 0.5
            is_green = 0.25 < h1 < 0.42 and s1 > 0.5
            partner_red = (0.95 < h2 or h2 < 0.05) and s2 > 0.5
            partner_green = 0.25 < h2 < 0.42 and s2 > 0.5
            if (is_red and partner_green) or (is_green and partner_red):
                issues.append({
                    'rule': 'AP-08',
                    'severity': 'error',
                    'message': 'Red-green colour combination detected',
                    'colours': [colour_list[i], colour_list[j]],
                })
    return issues
```

**Severity:** Warning (Error for red-green)

**Fix:** Use analogous or split-complementary colour schemes. Desaturate one of the complementary pair. Avoid red-green pairings entirely ([canva.com/colors/color-wheel](https://www.canva.com/colors/color-wheel/)).

---

### AP-09: Missing Speaker Notes

**Description:** Slides lack speaker notes, suggesting the deck may not be presentation-ready or relies entirely on the slides themselves.

**Why it's bad:** Speaker notes serve as memory cues during delivery. Their absence suggests the presenter may read from slides (leading to text-heavy slides) or that the deck is unfinished. Best practice: 30-60 words of notes per slide for standard presentations ([superchart.io](https://www.superchart.io/blog/speaker-notes), [duarte.com](https://www.duarte.com/blog/everything-need-know-using-speaker-notes-in-powerpoint/)).

**Detection Algorithm (python-pptx):**
```python
def check_speaker_notes(presentation, min_notes_pct=0.5):
    """At least 50% of content slides should have speaker notes."""
    total_content_slides = 0
    slides_with_notes = 0
    issues = []
    for slide in presentation.slides:
        # Skip likely title/divider slides (1 or fewer text shapes)
        text_shapes = [s for s in slide.shapes if s.has_text_frame and s.text_frame.text.strip()]
        if len(text_shapes) == 0:
            continue
        total_content_slides += 1
        notes_slide = slide.notes_slide
        if notes_slide and notes_slide.notes_text_frame.text.strip():
            slides_with_notes += 1
    if total_content_slides > 0:
        pct = slides_with_notes / total_content_slides
        if pct < min_notes_pct:
            issues.append({
                'rule': 'AP-09',
                'severity': 'warning',
                'message': f'Only {slides_with_notes}/{total_content_slides} content slides ({pct:.0%}) have speaker notes (minimum {min_notes_pct:.0%})',
            })
    return issues
```

**Severity:** Warning

**Fix:** Add concise speaker notes (keywords/phrases, not scripts) to each content slide. Target 30-60 words per slide.

---

### AP-10: Slide Count vs Talk Duration Mismatch

**Description:** The number of slides does not align with the expected talk duration, suggesting either too many slides (rushing) or too few (padding).

**Why it's bad:** The general rule is 1-2 minutes per slide. Guy Kawasaki's 10/20/30 Rule: 10 slides for 20 minutes. Having 40 slides for a 15-minute talk forces rushing; 5 slides for 45 minutes is padding ([storyfiner.com](https://storyfiner.com/the-perfect-slide-count-how-many-slides-for-a-10-minute-presentation/), [beautiful.ai](https://www.beautiful.ai/blog/what-is-the-10-20-30-rule-for-presentations-and-why-its-important-for-your-team)).

**Detection Algorithm:**
```python
def check_slide_count_ratio(presentation, duration_minutes=None,
                             min_ratio=0.5, max_ratio=2.0):
    """Check slide count vs duration. Expects 0.5-2 slides per minute."""
    if duration_minutes is None:
        return []  # Cannot check without duration metadata
    slide_count = len(presentation.slides)
    ratio = slide_count / duration_minutes
    issues = []
    if ratio > max_ratio:
        issues.append({
            'rule': 'AP-10',
            'severity': 'warning',
            'message': f'{slide_count} slides for {duration_minutes}min talk = {ratio:.1f} slides/min (max {max_ratio}). Too many slides.',
        })
    elif ratio < min_ratio:
        issues.append({
            'rule': 'AP-10',
            'severity': 'warning',
            'message': f'{slide_count} slides for {duration_minutes}min talk = {ratio:.1f} slides/min (min {min_ratio}). Too few slides.',
        })
    return issues
```

**Severity:** Warning

**Fix:** For a 10-minute talk: 7-12 slides. For 15 minutes: 10-15 slides. For 45 minutes: 25-40 slides.

---

### AP-11: Placeholder Residue

**Description:** Template placeholder text remains in the final deck: "Click to add title", "Lorem ipsum", "XXX", "TODO", "[insert]".

**Why it's bad:** Placeholder text is the most obvious sign of an unfinished presentation. It immediately destroys credibility.

**Detection Algorithm (python-pptx):**
```python
import re

PLACEHOLDER_PATTERNS = [
    r'click to add',
    r'lorem ipsum',
    r'\bXXX\b',
    r'\bTODO\b',
    r'\bTBD\b',
    r'\[insert\b',
    r'\[your .+?\]',
    r'placeholder',
    r'sample text',
    r'edit (this|here)',
    r'replace (this|with)',
    r'type (here|your)',
    r'add (your|text|title|subtitle|content)',
]

def check_placeholder_residue(slide):
    issues = []
    compiled = [re.compile(p, re.IGNORECASE) for p in PLACEHOLDER_PATTERNS]
    for shape in slide.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text.strip()
            for pattern in compiled:
                if pattern.search(text):
                    issues.append({
                        'rule': 'AP-11',
                        'severity': 'error',
                        'message': f'Placeholder text detected: "{text[:60]}"',
                        'shape_name': shape.name,
                    })
                    break
    return issues
```

**Severity:** Error

**Fix:** Replace all placeholder text with actual content or remove the element entirely.

---

### AP-12: Image Resolution Too Low for Placement Size

**Description:** An image is placed at a size that requires more pixels than the source image provides, resulting in visible blurriness or pixelation.

**Why it's bad:** When images are enlarged beyond their native resolution, PowerPoint interpolates (invents) pixels, causing blurriness. For HD projection (1920x1080), a full-bleed image must be at least 1920x1080 pixels. DPI is irrelevant for screen display; only pixel dimensions matter ([brightcarbon.com](https://www.brightcarbon.com/blog/powerpoint-picture-size-and-resolution/), [rdpslides.com](https://www.rdpslides.com/pptfaq/FAQ00415_What-s_the_best_resolution_for_images_in_PowerPoint_screen_shows-_.htm)).

**Detection Algorithm (python-pptx):**
```python
from pptx.util import Inches, Emu
from PIL import Image
import io

def check_image_resolution(slide, presentation, min_dpi_equiv=96):
    """Check that images have sufficient resolution for their placement size."""
    issues = []
    slide_width_in = presentation.slide_width / 914400  # EMU to inches
    slide_height_in = presentation.slide_height / 914400

    for shape in slide.shapes:
        if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
            image = shape.image
            img_blob = image.blob
            pil_img = Image.open(io.BytesIO(img_blob))
            img_w, img_h = pil_img.size

            # Shape placement size in inches
            place_w_in = shape.width / 914400
            place_h_in = shape.height / 914400

            # Effective DPI at placement size
            eff_dpi_x = img_w / place_w_in if place_w_in > 0 else 999
            eff_dpi_y = img_h / place_h_in if place_h_in > 0 else 999

            # For HD 1920x1080 output, need at least 150 DPI effective
            # Full-bleed (10" wide) needs 1920px = 192 DPI
            if eff_dpi_x < min_dpi_equiv or eff_dpi_y < min_dpi_equiv:
                issues.append({
                    'rule': 'AP-12',
                    'severity': 'error',
                    'message': f'Image {img_w}x{img_h}px at {place_w_in:.1f}"x{place_h_in:.1f}" = {eff_dpi_x:.0f}x{eff_dpi_y:.0f} DPI (min {min_dpi_equiv})',
                    'shape_name': shape.name,
                })
    return issues
```

**Severity:** Error

**Fix:** Replace with higher-resolution image. Minimum pixel requirements by placement zone:

| Placement | Minimum Pixels |
|-----------|---------------|
| Full-bleed background | 1920 x 1080 |
| Half-slide image | 960 x 1080 |
| Quarter-slide image | 960 x 540 |
| Thumbnail/icon | 300 x 300 |

---

### AP-13: Image Aspect Ratio Distortion

**Description:** An image's display aspect ratio differs significantly from its native aspect ratio, causing it to appear stretched or squished.

**Why it's bad:** Distorted images look unprofessional and can misrepresent data in charts or diagrams. Even a few percent distortion is noticeable on faces and circular objects ([web.dev](https://web.dev/image-aspect-ratio/)).

**Detection Algorithm (python-pptx):**
```python
from PIL import Image
import io

def check_aspect_ratio_distortion(slide, max_distortion_pct=5.0):
    issues = []
    for shape in slide.shapes:
        if shape.shape_type == 13:  # Picture
            image = shape.image
            pil_img = Image.open(io.BytesIO(image.blob))
            native_w, native_h = pil_img.size
            native_ratio = native_w / native_h if native_h > 0 else 1

            display_w = shape.width
            display_h = shape.height
            display_ratio = display_w / display_h if display_h > 0 else 1

            distortion_pct = abs(native_ratio - display_ratio) / native_ratio * 100
            if distortion_pct > max_distortion_pct:
                issues.append({
                    'rule': 'AP-13',
                    'severity': 'warning',
                    'message': f'Image distorted by {distortion_pct:.1f}% (native {native_w}:{native_h}, displayed {display_w}:{display_h})',
                    'shape_name': shape.name,
                })
    return issues
```

**Severity:** Warning

**Fix:** Lock aspect ratio when resizing images. Use crop instead of stretch to fit desired dimensions.

---

### AP-14: Too Many Bullet Points

**Description:** A single slide has more than 5-6 bullet points, exceeding working memory capacity.

**Why it's bad:** George Miller's research (1956) established the 7+/-2 working memory limit. Eye-tracking studies show that as bullet count increases, audience engagement wanes — they read only a fraction of the content. The 5-5-5 rule recommends maximum 5 bullets per slide ([twistly.ai](https://twistly.ai/the-rule-of-seven-optimal-slide-content-for-maximum-retention/), [slidesai.io](https://www.slidesai.io/blog/the-5-5-5-rule-powerpoint), [innerdrive.co.uk](https://www.innerdrive.co.uk/blog/tracking-powerpoint-attention/)).

**Detection Algorithm (python-pptx):**
```python
def check_bullet_count(slide, max_bullets=6):
    issues = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            bullet_count = 0
            for para in shape.text_frame.paragraphs:
                text = para.text.strip()
                if text and para.level >= 0:
                    # Count non-empty paragraphs as potential bullets
                    pPr = para._pPr
                    has_bullet = pPr is not None and (
                        pPr.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}buChar') is not None or
                        pPr.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}buAutoNum') is not None
                    )
                    if has_bullet:
                        bullet_count += 1
            if bullet_count > max_bullets:
                issues.append({
                    'rule': 'AP-14',
                    'severity': 'warning',
                    'message': f'{bullet_count} bullet points (max {max_bullets})',
                    'shape_name': shape.name,
                })
    return issues
```

**Severity:** Warning

**Fix:** Split into multiple slides or convert bullets into visual elements (icons, diagrams, timelines).

---

### AP-15: Consecutive Bullet-Heavy Slides

**Description:** Three or more consecutive slides are all bullet-point lists, creating visual monotony.

**Why it's bad:** Visual monotony causes most audiences to disengage. If every slide looks the same, the audience quickly tunes out. Research confirms visual slides are more effective — subjects exposed to graphics pay more attention and recall more than those seeing bulleted lists ([visme.co](https://visme.co/blog/bullet-points-presentation/), [ethos3.com](https://ethos3.com/why-bullet-points-kill-presentations/)).

**Detection Algorithm (python-pptx):**
```python
def check_consecutive_bullet_slides(presentation, max_consecutive=3):
    issues = []
    consecutive = 0
    for i, slide in enumerate(presentation.slides):
        is_bullet_heavy = False
        for shape in slide.shapes:
            if shape.has_text_frame:
                bullet_count = sum(1 for p in shape.text_frame.paragraphs
                                   if p.text.strip() and p._pPr is not None)
                if bullet_count >= 4:
                    is_bullet_heavy = True
                    break
        if is_bullet_heavy:
            consecutive += 1
        else:
            consecutive = 0
        if consecutive >= max_consecutive:
            issues.append({
                'rule': 'AP-15',
                'severity': 'warning',
                'message': f'{consecutive} consecutive bullet-heavy slides ending at slide {i + 1}',
            })
    return issues
```

**Severity:** Warning

**Fix:** Intersperse bullet slides with visual slides (images, diagrams, quotes, data visualisations). Follow the 5-5-5 rule: no more than 5 text-heavy slides in a row.

---

### AP-16: Missing Title Slide

**Description:** The first slide of the deck is not a title/cover slide.

**Why it's bad:** The title slide establishes the topic, the speaker's identity, and the visual brand. Its absence confuses the audience and violates standard presentation structure ([colorado.edu](https://www.colorado.edu/digital-accessibility/resources/understanding-powerpoint-accessibility), [bati-itao.github.io](https://bati-itao.github.io/resources/best-practices-powerpoint-en.html)).

**Detection Algorithm (python-pptx):**
```python
def check_title_slide(presentation):
    issues = []
    if len(presentation.slides) == 0:
        return [{'rule': 'AP-16', 'severity': 'error', 'message': 'Presentation has no slides'}]
    first_slide = presentation.slides[0]
    layout_name = first_slide.slide_layout.name.lower()
    has_title_layout = 'title' in layout_name
    has_title_placeholder = any(
        hasattr(shape, 'placeholder_format') and
        shape.placeholder_format is not None and
        shape.placeholder_format.idx == 0
        for shape in first_slide.shapes
    )
    if not has_title_layout and not has_title_placeholder:
        issues.append({
            'rule': 'AP-16',
            'severity': 'warning',
            'message': 'First slide does not appear to be a title slide',
        })
    return issues
```

**Severity:** Warning

**Fix:** Ensure the first slide uses the Title Slide layout with presentation title, speaker name, and event/date.

---

### AP-17: Missing Closing/CTA Slide

**Description:** The deck ends abruptly without a closing slide, summary, or call-to-action.

**Why it's bad:** Ending with "Thank you" alone is a wasted opportunity. A CTA slide with 2-3 specific asks drives audience action. Contact information should be provided for follow-up ([crappypresentations.com](https://www.crappypresentations.com/presentation-tips-and-tricks/10-presentation-mistakes), [W3C WAI](https://www.w3.org/WAI/teach-advocate/accessible-presentations/)).

**Detection Algorithm (python-pptx):**
```python
CTA_KEYWORDS = ['contact', 'email', 'questions', 'next steps', 'call to action',
                'thank you', 'thanks', 'get in touch', 'follow up', 'resources',
                'learn more', 'summary', 'key takeaways', 'conclusion']

def check_closing_slide(presentation):
    issues = []
    if len(presentation.slides) < 2:
        return issues
    last_slide = presentation.slides[-1]
    all_text = ' '.join(
        shape.text_frame.text.lower()
        for shape in last_slide.shapes if shape.has_text_frame
    )
    has_cta = any(kw in all_text for kw in CTA_KEYWORDS)
    if not has_cta:
        issues.append({
            'rule': 'AP-17',
            'severity': 'warning',
            'message': 'Last slide does not appear to be a closing/CTA slide',
        })
    return issues
```

**Severity:** Warning

**Fix:** Add a closing slide with: summary of key points, specific calls to action, contact information/links.

---

### AP-18: Inconsistent Heading Sizes

**Description:** Title/heading text varies in size across slides without a clear hierarchical reason.

**Why it's bad:** Inconsistent heading sizes break visual hierarchy. If H2 tags are 24pt on one slide, they should remain 24pt across all slides. Maintain a consistent scale (e.g. 1.25-1.5x increase between heading levels) ([hanjing.medium.com](https://hanjing.medium.com/font-sizing-4259801c04c1), [columbia.edu](https://visualidentity.columbia.edu/content/headings)).

**Detection Algorithm (python-pptx):**
```python
from collections import Counter

def check_heading_consistency(presentation, max_variance_pt=2):
    """Check that title placeholders use consistent font sizes across slides."""
    title_sizes = []
    for slide in presentation.slides:
        for shape in slide.shapes:
            if (hasattr(shape, 'placeholder_format') and
                shape.placeholder_format is not None and
                shape.placeholder_format.idx == 0):  # Title placeholder
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if run.font.size:
                            title_sizes.append(run.font.size.pt)
    issues = []
    if title_sizes:
        most_common_size = Counter(title_sizes).most_common(1)[0][0]
        outliers = [s for s in title_sizes if abs(s - most_common_size) > max_variance_pt]
        if outliers:
            issues.append({
                'rule': 'AP-18',
                'severity': 'warning',
                'message': f'Title sizes vary: most common {most_common_size}pt but found {set(outliers)}pt',
            })
    return issues
```

**Severity:** Warning

**Fix:** Standardise heading sizes via the slide master. Recommended: H1 32pt, H2 24pt, H3 20pt.

---

### AP-19: Text Overflow/Clipping

**Description:** Text content exceeds its container, causing text to be clipped, hidden, or auto-shrunk.

**Why it's bad:** Clipped text loses content. Auto-shrunk text may become illegibly small. PowerPoint's `horzOverflow` can be set to "clip" in the XML, silently hiding content ([python-pptx docs](https://python-pptx.readthedocs.io/en/latest/dev/analysis/txt-autofit-text.html)).

**Detection Algorithm (python-pptx):**
```python
from lxml import etree

def check_text_overflow(slide):
    issues = []
    nsmap = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
    for shape in slide.shapes:
        if shape.has_text_frame:
            # Check for autofit shrink (indicates text was too large)
            tf_xml = shape.text_frame._txBody
            bodyPr = tf_xml.find('.//a:bodyPr', nsmap)
            if bodyPr is not None:
                autofit = bodyPr.get('autoFit') or bodyPr.find('a:normAutofit', nsmap)
                if autofit is not None:
                    # normAutofit with fontScale < 100% means text was shrunk
                    norm = bodyPr.find('a:normAutofit', nsmap)
                    if norm is not None:
                        scale = norm.get('fontScale')
                        if scale and int(scale) < 90000:  # < 90% (stored as 90000)
                            issues.append({
                                'rule': 'AP-19',
                                'severity': 'warning',
                                'message': f'Text auto-shrunk to {int(scale)/1000:.0f}% to fit container',
                                'shape_name': shape.name,
                            })
    return issues
```

**Severity:** Warning

**Fix:** Reduce text content to fit naturally, or increase the container size. Never rely on auto-shrink.

---

### AP-20: Element Overlap

**Description:** Two or more elements overlap on the slide in a way that obscures content.

**Why it's bad:** Overlapping elements hide information and create visual clutter. While intentional overlap can be a design choice (e.g. text over an image with overlay), unintentional overlap is a bug.

**Detection Algorithm (python-pptx):**
```python
def check_element_overlap(slide, min_overlap_pct=25):
    """Check for shapes that overlap more than min_overlap_pct."""
    shapes_with_content = []
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            shapes_with_content.append({
                'name': shape.name,
                'left': shape.left, 'top': shape.top,
                'right': shape.left + shape.width,
                'bottom': shape.top + shape.height,
                'area': shape.width * shape.height,
            })

    issues = []
    for i in range(len(shapes_with_content)):
        for j in range(i + 1, len(shapes_with_content)):
            a, b = shapes_with_content[i], shapes_with_content[j]
            # Calculate intersection
            x_overlap = max(0, min(a['right'], b['right']) - max(a['left'], b['left']))
            y_overlap = max(0, min(a['bottom'], b['bottom']) - max(a['top'], b['top']))
            overlap_area = x_overlap * y_overlap
            smaller_area = min(a['area'], b['area'])
            if smaller_area > 0:
                overlap_pct = (overlap_area / smaller_area) * 100
                if overlap_pct > min_overlap_pct:
                    issues.append({
                        'rule': 'AP-20',
                        'severity': 'warning',
                        'message': f'Elements "{a["name"]}" and "{b["name"]}" overlap by {overlap_pct:.0f}%',
                    })
    return issues
```

**Severity:** Warning

**Fix:** Reposition elements to eliminate unintentional overlap. Use alignment guides and grid snapping.

---

### AP-21: Excessive Animations

**Description:** The deck uses too many different animation types or transitions, or applies flashy effects that distract from content.

**Why it's bad:** Overusing transitions overwhelms the audience and undermines credibility. Professional presentations should use 1-2 transition types maximum. "Fade" is appropriate for formal settings. Flashy animations are seen as getting in the way of content ([rekarda.com](https://www.rekarda.com/blog/mastering-powerpoint-animation-best-practices-tips-and-common-pitfalls), [verdanabold.com](https://www.verdanabold.com/post/the-do-s-and-dont-s-of-powerpoint-animation)).

**Detection Algorithm (python-pptx):**
```python
from lxml import etree

def check_excessive_animations(presentation, max_transition_types=2):
    transition_types = set()
    animation_count = 0
    nsmap = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}

    for slide in presentation.slides:
        slide_xml = slide._element
        # Check transitions
        transition = slide_xml.find('.//p:transition', nsmap)
        if transition is not None:
            for child in transition:
                transition_types.add(etree.QName(child).localname)
        # Count animations
        timing = slide_xml.find('.//p:timing', nsmap)
        if timing is not None:
            anims = timing.findall('.//', nsmap)
            animation_count += len(anims)

    issues = []
    if len(transition_types) > max_transition_types:
        issues.append({
            'rule': 'AP-21',
            'severity': 'warning',
            'message': f'{len(transition_types)} different transition types (max {max_transition_types}): {", ".join(transition_types)}',
        })
    return issues
```

**Severity:** Warning

**Fix:** Limit to 1-2 subtle transition types (Fade, Push). Remove all gimmicky effects (Spin, Bounce, Swivel). Apply transitions consistently.

---

### AP-22: Poor Data-Ink Ratio on Charts

**Description:** Charts contain excessive non-data elements (heavy gridlines, 3D effects, decorative borders, unnecessary legends) that obscure the actual data.

**Why it's bad:** Edward Tufte's data-ink ratio principle: maximise the proportion of ink devoted to actual data information. Chart junk (moiré patterns, heavy grids, 3D effects) distracts from the data without adding information ([thedoublethink.com](https://thedoublethink.com/tuftes-principles-for-visualizing-quantitative-information/), [holistics.io](https://www.holistics.io/blog/data-ink-ratio/)).

**Detection Algorithm (python-pptx):**
```python
from lxml import etree

def check_chart_junk(slide):
    """Flag charts with 3D effects, heavy gridlines, or excessive decoration."""
    issues = []
    nsmap = {
        'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    }
    for shape in slide.shapes:
        if shape.has_chart:
            chart_xml = shape.chart._element
            # Check for 3D effects
            view3D = chart_xml.find('.//c:view3D', nsmap)
            if view3D is not None:
                issues.append({
                    'rule': 'AP-22',
                    'severity': 'warning',
                    'message': '3D chart effects detected — reduces data-ink ratio',
                    'shape_name': shape.name,
                })
            # Check for heavy gridlines
            major_gridlines = chart_xml.findall('.//c:majorGridlines', nsmap)
            minor_gridlines = chart_xml.findall('.//c:minorGridlines', nsmap)
            if minor_gridlines:
                issues.append({
                    'rule': 'AP-22',
                    'severity': 'info',
                    'message': 'Minor gridlines detected — consider removing for cleaner chart',
                    'shape_name': shape.name,
                })
    return issues
```

**Severity:** Warning

**Fix:** Remove 3D effects, minor gridlines, decorative borders. Use direct labelling instead of legends where possible. Aim for data-ink ratio close to 1.0.

---

### AP-23: Logos/Branding Missing or Inconsistent

**Description:** Company logos are missing from slides that should have them, or logos appear at different sizes/positions across slides.

**Why it's bad:** Inconsistent branding signals unprofessional work. Logos should be placed on the slide master to ensure they appear at the same size and position on every slide ([brand.jhu.edu](https://brand.jhu.edu/blog/building-effective-presentations-with-a-branded-powerpoint-template/), [learn.aippt.com](https://learn.aippt.com/using-powerpoints-master-slides-for-consistent-branding/)).

**Detection Algorithm (python-pptx):**
```python
def check_branding_consistency(presentation, expected_logo_name=None):
    """Check that logo appears consistently across slides."""
    issues = []
    logo_positions = []
    slides_without_logo = []

    for i, slide in enumerate(presentation.slides):
        found_logo = False
        for shape in slide.shapes:
            name_lower = shape.name.lower()
            if ('logo' in name_lower or
                (expected_logo_name and expected_logo_name.lower() in name_lower)):
                found_logo = True
                logo_positions.append({
                    'slide': i + 1,
                    'left': shape.left, 'top': shape.top,
                    'width': shape.width, 'height': shape.height,
                })
        if not found_logo:
            slides_without_logo.append(i + 1)

    # Check consistency of position/size
    if logo_positions and len(logo_positions) >= 2:
        ref = logo_positions[0]
        for pos in logo_positions[1:]:
            if (abs(pos['left'] - ref['left']) > 914400 // 10 or  # > 0.1 inch
                abs(pos['top'] - ref['top']) > 914400 // 10):
                issues.append({
                    'rule': 'AP-23',
                    'severity': 'info',
                    'message': f'Logo position varies between slide 1 and slide {pos["slide"]}',
                })
    return issues
```

**Severity:** Info

**Fix:** Place logos on the slide master. Do not stretch, recolour, or reposition logos per-slide.

---

### AP-24: Dead/Empty Slides

**Description:** Slides with no meaningful content — blank slides, slides with only empty placeholders, or slides with only a background colour.

**Why it's bad:** Empty slides waste audience time and break presentation flow. They often result from accidental duplication or incomplete editing ([slidespeak.co](https://slidespeak.co/free-tools/remove-empty-shapes-powerpoint-online)).

**Detection Algorithm (python-pptx):**
```python
def check_dead_slides(slide, slide_number):
    """Check if a slide has no meaningful content."""
    meaningful_content = False
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            meaningful_content = True
            break
        if shape.shape_type == 13:  # Picture
            meaningful_content = True
            break
        if hasattr(shape, 'has_chart') and shape.has_chart:
            meaningful_content = True
            break
        if hasattr(shape, 'has_table') and shape.has_table:
            meaningful_content = True
            break

    issues = []
    if not meaningful_content:
        issues.append({
            'rule': 'AP-24',
            'severity': 'warning',
            'message': f'Slide {slide_number} appears to have no meaningful content',
        })
    return issues
```

**Severity:** Warning

**Fix:** Remove empty slides or populate them with content. Check for intentional section dividers (which should have at least a heading).

---

### AP-25: Colour Accessibility (Colourblind-Safe Palette Check)

**Description:** The colour palette used in the deck is not safe for viewers with colour vision deficiency (CVD).

**Why it's bad:** Approximately 8% of men and 0.5% of women have some form of colour blindness, most commonly red-green (deuteranopia/protanopia). Using red and green as the only differentiators makes content invisible to these viewers ([davidmathlogic.com](https://davidmathlogic.com/colorblind/), [visme.co](https://visme.co/blog/color-blind-friendly-palette/), [jakubnowosad.com](https://jakubnowosad.com/colorblindcheck/)).

**Detection Algorithm:**
```python
import colorsys

def simulate_deuteranopia(r, g, b):
    """Simplified deuteranopia simulation (Brettel et al.)."""
    # Linearize sRGB
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    rl, gl, bl = lin(r), lin(g), lin(b)
    # Simplified deuteranopia transform matrix
    r2 = 0.625 * rl + 0.375 * gl + 0.0 * bl
    g2 = 0.7 * rl + 0.3 * gl + 0.0 * bl
    b2 = 0.0 * rl + 0.3 * gl + 0.7 * bl
    # Convert back (simplified)
    def delin(c):
        c = max(0, min(1, c))
        return int((c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1/2.4) - 0.055) * 255)
    return (delin(r2), delin(g2), delin(b2))

def check_colourblind_safety(colours_used, min_distance=30):
    """Check that colours remain distinguishable under CVD simulation."""
    issues = []
    colour_list = list(colours_used)
    for i in range(len(colour_list)):
        for j in range(i + 1, len(colour_list)):
            sim_i = simulate_deuteranopia(*colour_list[i])
            sim_j = simulate_deuteranopia(*colour_list[j])
            # Euclidean distance in simulated space
            dist = sum((a - b) ** 2 for a, b in zip(sim_i, sim_j)) ** 0.5
            if dist < min_distance:
                issues.append({
                    'rule': 'AP-25',
                    'severity': 'warning',
                    'message': f'Colours {colour_list[i]} and {colour_list[j]} may be indistinguishable for deuteranopia viewers (distance: {dist:.0f})',
                })
    return issues
```

**Severity:** Warning

**Fix:** Use a colourblind-safe palette. Safe hues: blue + orange (not red + green). Apply the 60-30-10 rule. Use patterns alongside colours for redundant encoding. Test with a CVD simulator ([mk.bcgsc.ca](https://mk.bcgsc.ca/colorblind/palettes.mhtml)).

---

## 2. WCAG Contrast at Projection Distance

### Standard WCAG Requirements

| Level | Normal Text | Large Text (18pt+ or 14pt+ bold) |
|-------|------------|----------------------------------|
| **AA** | 4.5:1 minimum | 3:1 minimum |
| **AAA** | 7:1 minimum | 4.5:1 minimum |

Large text is defined as 18pt (24px) or 14pt bold (18.5px) or larger ([W3C WCAG 1.4.3](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)).

### Projection Adjustments

Projectors introduce significant contrast degradation:

1. **Washout factor:** Colours projected are 20-30% lighter than on a monitor due to projector light and ambient light in the room ([thinkoutsidetheslide.com](https://www.thinkoutsidetheslide.com/five-common-problems-with-poor-display-of-powerpoint-presentations/)).

2. **Ambient light:** Conference rooms average 250 lux of ambient light. The IES recommends 300-500 lux for meeting rooms. This ambient light raises the black level and reduces effective contrast ratio ([BenQ](https://www.benq.com/en-ap/knowledge-center/knowledge/projector-specs-explained.html)).

3. **Projector contrast ratio:** Conference projectors typically have 3,000-5,000:1 native contrast ratio, but effective on-screen contrast in a lit room drops to ~500:1 or lower.

### Recommended Ratios for Conference Presentations

| Content | Recommended Minimum |
|---------|-------------------|
| Normal text on solid background | **7:1** (WCAG AAA) |
| Large text (24pt+) on solid background | **4.5:1** |
| Text over images/gradients | **7:1** with overlay |
| Critical data/numbers | **10:1** |

**Rationale:** Since projectors degrade contrast by ~30-50%, designing to WCAG AAA (7:1) ensures the projected result remains above the AA threshold (4.5:1).

### Contrast Ratio Calculation Algorithm

```python
def relative_luminance(r, g, b):
    """
    Calculate relative luminance per WCAG 2.0.
    Input: R, G, B values 0-255
    Output: Luminance 0.0-1.0
    Source: W3C WCAG 2.0 G17 technique
    """
    def linearize(c):
        c_srgb = c / 255.0
        if c_srgb <= 0.03928:
            return c_srgb / 12.92
        else:
            return ((c_srgb + 0.055) / 1.055) ** 2.4

    R = linearize(r)
    G = linearize(g)
    B = linearize(b)
    return 0.2126 * R + 0.7152 * G + 0.0722 * B

def contrast_ratio(rgb1, rgb2):
    """
    Calculate WCAG contrast ratio.
    Returns value between 1.0 (no contrast) and 21.0 (maximum).
    IMPORTANT: Do not round — 4.499:1 does NOT meet 4.5:1.
    Source: https://www.w3.org/TR/WCAG20-TECHS/G17.html
    """
    L1 = relative_luminance(*rgb1)
    L2 = relative_luminance(*rgb2)
    lighter = max(L1, L2)
    darker = min(L1, L2)
    return (lighter + 0.05) / (darker + 0.05)
```

### Colour Combinations That Fail on Projection

| Combination | Screen Ratio | Projected Ratio (est.) | Verdict |
|------------|-------------|----------------------|---------|
| Light grey (#999) on white (#FFF) | 2.8:1 | ~2.0:1 | FAIL |
| Red (#FF0000) on black (#000) | 5.3:1 | ~3.5:1 | FAIL |
| Green (#00AA00) on white (#FFF) | 3.8:1 | ~2.5:1 | FAIL |
| Yellow (#FFFF00) on white (#FFF) | 1.1:1 | ~1.0:1 | FAIL |
| Navy (#003366) on white (#FFF) | 12.0:1 | ~8.0:1 | PASS |
| White (#FFFFFF) on dark blue (#1a1a4e) | 14.7:1 | ~10.0:1 | PASS |
| Black (#000) on white (#FFF) | 21.0:1 | ~14.0:1 | PASS |

**Sources:** [W3C WCAG 2.1](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html), [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/), [ADG](https://www.accessibility-developer-guide.com/knowledge/colours-and-contrast/how-to-calculate/), [Vanderbilt Edge for Scholars](https://edgeforscholars.vumc.org/optimizing-colors-for-projected-presentations/), [Microsoft Support](https://support.microsoft.com/en-us/office/combining-colors-in-powerpoint-mistakes-to-avoid-555e1689-85a7-4b2e-aa89-db5270528852)

---

## 3. Professional AV Specifications

### Standard Resolutions

| Resolution | Name | Use Case |
|-----------|------|----------|
| 1920 x 1080 | Full HD (1080p) | Standard conference projector |
| 2560 x 1440 | QHD (1440p) | High-end conference rooms |
| 3840 x 2160 | 4K UHD | Large venues, LED walls |

Most conferences use **1920x1080** as the standard. Design for this and export at matching resolution ([aspectratiocalculatorpro.com](https://aspectratiocalculatorpro.com/presentation-aspect-ratio-powerpoint/)).

### Aspect Ratios

| Ratio | Dimensions (inches) | Status |
|-------|---------------------|--------|
| **16:9** | 13.333" x 7.5" | **Standard** — matches laptops, Zoom/Teams, YouTube, TVs, most projectors |
| 16:10 | 13.333" x 8.333" | Legacy — some Apple displays |
| 4:3 | 10" x 7.5" | Obsolete — avoid |

**Rule:** Always use 16:9. Export resolution must match slide ratio (e.g. 1920x1080 for 16:9).

### Safe Margins

| Zone | Inset from Edge | Purpose |
|------|----------------|---------|
| **Action Safe** | 5% (0.67" on 13.33" width) | All meaningful content |
| **Title Safe** | 10% (1.33" on 13.33" width) | All text and logos |
| Full Bleed | 0% | Background images only |

**Source:** [Cinebox Safe Areas](https://www.cinebox.co/help/safeArea), [NAB Television Safe Areas](https://www.nab.org/xert/scitech/pdfs/tv031510.pdf), [ITU-R BT.1848](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1848-1-201510-I!!PDF-E.pdf)

### File Size Limits

| Context | Typical Limit |
|---------|---------------|
| Email attachment | 10-25 MB |
| Conference upload portal | 50-200 MB |
| SPIE conferences | No limit |
| General best practice | < 100 MB |

### Font Requirements

- **Embed fonts** in the PPTX file to prevent substitution on the presentation computer
- Embedding increases file size significantly
- Use **system-safe fonts** when possible: Arial, Calibri, Verdana, Tahoma, Helvetica, Georgia
- Avoid custom or purchased fonts that may not be on the session computer
- Conference session computers typically have Windows 10/11 standard font sets

**Source:** [ARL Guidelines](https://www.arl.org/accessibility-guidelines-for-powerpoint-presentations/), [SPIE Oral Presentation Guidelines](https://lux.spie.org/conferences-and-exhibitions/optifab/presenters/prepare-to-present/oral-presentation-guidelines), [Neuxpower](https://support.neuxpower.com/hc/en-us/articles/360007786978-Embed-subset-or-remove-embedded-fonts-in-PowerPoint-or-Word)

### Video/Animation Compatibility

- Some conferences prohibit embedded video
- Embedded MP4 (H.264) is most compatible
- Animations may not render on non-Windows systems
- Test on the venue's presentation system before going live

### Projector Specifications (Typical Conference Room)

| Specification | Typical Value |
|--------------|--------------|
| Brightness | 3,500-5,000 ANSI lumens |
| Native contrast ratio | 3,000:1 - 5,000:1 |
| Effective contrast (lit room) | ~500:1 |
| Resolution | 1920x1080 (Full HD) |
| Ambient light | 250-500 lux |

**Source:** [BenQ Projector Specs](https://www.benq.com/en-ap/knowledge-center/knowledge/projector-specs-explained.html), [ViewSonic Lumens Guide](https://www.viewsonic.com/library/tech/what-are-lumens-and-how-to-use-them-to-choose-a-projector/)

---

## 4. Image Quality Thresholds

### BRISQUE Score Thresholds

BRISQUE (Blind/Referenceless Image Spatial Quality Evaluator) is a no-reference image quality metric.

| Score Range | Quality | Slide Use |
|------------|---------|-----------|
| 0-20 | Excellent | Any placement |
| 20-35 | Good | Full-bleed and feature images |
| 35-45 | Acceptable | Small images and thumbnails |
| 45-60 | Poor | Reject — replace image |
| 60-100 | Very poor | Reject |

**Threshold for deck-qa:** BRISQUE < 35 for feature images, < 45 for thumbnails.

**Python implementation:**
```python
# Using opencv-contrib-python
import cv2

def compute_brisque(image_path):
    img = cv2.imread(image_path)
    brisque = cv2.quality.QualityBRISQUE_compute(
        img,
        "brisque_model_live.yml",
        "brisque_range_live.yml"
    )
    return brisque[0][0]  # Score 0-100, lower is better

# Alternative using pybrisque
from brisque import BRISQUE
brisque = BRISQUE()
score = brisque.score(img)
```

**Sources:** [MATLAB BRISQUE](https://www.mathworks.com/help/images/ref/brisque.html), [LearnOpenCV](https://learnopencv.com/image-quality-assessment-brisque/), [OpenCV QualityBRISQUE](https://docs.opencv.org/4.x/d8/d99/classcv_1_1quality_1_1QualityBRISQUE.html), [Original Paper (UTAustin)](https://live.ece.utexas.edu/publications/2012/TIP%20BRISQUE.pdf)

### Minimum Resolution Per Placement Zone

| Placement Zone | Min Width | Min Height | Notes |
|---------------|-----------|------------|-------|
| Full-bleed background | 1920 px | 1080 px | Must match output resolution |
| Half-slide hero image | 960 px | 1080 px | Or 1920x540 for horizontal |
| Quarter-slide image | 960 px | 540 px | |
| Inline image | 480 px | 480 px | |
| Thumbnail/icon | 300 px | 300 px | |
| Logo | 200 px | 200 px | Vector (SVG/EMF) preferred |

**Source:** [BrightCarbon](https://www.brightcarbon.com/blog/powerpoint-picture-size-and-resolution/)

### Compression Artifact Detection

JPEG compression creates blocking artifacts at 8x8 pixel block boundaries. Detection approaches:

```python
import numpy as np
import cv2

def detect_jpeg_blockiness(image_path, threshold=5.0):
    """
    Detect JPEG block boundary artifacts.
    Measures discontinuity at 8x8 block boundaries.
    Returns blockiness score (higher = more artifacts).
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    h, w = img.shape

    # Measure horizontal block boundary discontinuities
    h_diffs = []
    for x in range(8, w, 8):
        if x < w:
            diff = np.abs(img[:, x].astype(float) - img[:, x-1].astype(float))
            h_diffs.append(np.mean(diff))

    # Measure vertical block boundary discontinuities
    v_diffs = []
    for y in range(8, h, 8):
        if y < h:
            diff = np.abs(img[y, :].astype(float) - img[y-1, :].astype(float))
            v_diffs.append(np.mean(diff))

    blockiness = (np.mean(h_diffs) + np.mean(v_diffs)) / 2
    return blockiness  # > threshold indicates visible compression artifacts
```

**Source:** [Wikipedia: Compression artifact](https://en.wikipedia.org/wiki/Compression_artifact), [IEEE: Block boundary discontinuity](https://ieeexplore.ieee.org/document/678634/)

### Upscaled-from-Thumbnail Detection

Upscaled images lack high-frequency detail and exhibit characteristic smoothness:

```python
import cv2
import numpy as np

def detect_upscaling(image_path, blur_threshold=100.0):
    """
    Detect likely upscaled images using Laplacian variance.
    Low variance = smooth/blurry = likely upscaled from small original.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()

    # Also check for interpolation artifacts
    # Upscaled images have unnaturally smooth gradients
    sobel_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
    edge_density = np.mean(np.sqrt(sobel_x**2 + sobel_y**2))

    return {
        'laplacian_variance': laplacian_var,
        'edge_density': edge_density,
        'likely_upscaled': laplacian_var < blur_threshold,
    }
```

**Source:** [Image scaling (Wikipedia)](https://en.wikipedia.org/wiki/Image_scaling)

---

## 5. Automated Visual Regression Testing

### Pixelmatch for Slide Comparison

Pixelmatch is a fast pixel-by-pixel image comparison library. A 1280x720 screenshot compares in under 50ms.

**Use cases for deck QA:**
- Compare generated slides against golden reference renders
- Detect unintended visual changes between deck versions
- Verify consistent layout across slide variants

**Integration:**
```javascript
const pixelmatch = require('pixelmatch');
const { PNG } = require('pngjs');
const fs = require('fs');

function compareSlideImages(expectedPath, actualPath, diffPath) {
    const expected = PNG.sync.read(fs.readFileSync(expectedPath));
    const actual = PNG.sync.read(fs.readFileSync(actualPath));
    const { width, height } = expected;
    const diff = new PNG({ width, height });

    const numDiffPixels = pixelmatch(
        expected.data, actual.data, diff.data,
        width, height,
        { threshold: 0.1 }  // Anti-aliasing tolerance
    );

    fs.writeFileSync(diffPath, PNG.sync.write(diff));
    const diffPercent = (numDiffPixels / (width * height)) * 100;
    return { numDiffPixels, diffPercent };
}
```

**Source:** [Pixelmatch (npm)](https://www.npmjs.com/package/pixelmatch), [Playwright Visual Testing](https://vitest.dev/guide/browser/visual-regression-testing), [jest-image-snapshot](https://github.com/americanexpress/jest-image-snapshot)

### Perceptual Hashing for Slide Similarity

Perceptual hashing (pHash) creates fingerprints that are similar for visually similar images, unlike cryptographic hashes where any change produces a completely different hash.

**Algorithm (pHash):**
1. Resize image to 32x32 pixels
2. Convert to grayscale
3. Apply Discrete Cosine Transform (DCT)
4. Extract low-frequency components
5. Generate binary hash by comparing values to threshold

**Comparison:** Hamming distance between hashes. Low distance = similar images.

```python
from PIL import Image
import imagehash

def compute_phash(image_path):
    """Compute perceptual hash for slide image."""
    img = Image.open(image_path)
    return imagehash.phash(img)

def compare_slides(path_a, path_b, max_distance=10):
    """Compare two slide renders. Distance < 10 = 'approximately the same'."""
    hash_a = compute_phash(path_a)
    hash_b = compute_phash(path_b)
    distance = hash_a - hash_b  # Hamming distance
    return {
        'distance': distance,
        'similar': distance <= max_distance,
    }
```

pHash is tolerant of minor modifications (< 25% of the image) including compression, scaling, and watermarking, but struggles with heavy cropping or mirroring.

**Source:** [Perceptual hashing (Wikipedia)](https://en.wikipedia.org/wiki/Perceptual_hashing), [pHash.org](https://www.phash.org/docs/pubs/thesis_zauner.pdf), [Cloudinary pHash](https://cloudinary.com/blog/how_to_automatically_identify_similar_images_using_phash)

### Headless PPTX-to-Image Rendering

**Pipeline: PPTX -> PDF -> Images**

```bash
# Step 1: PPTX to PDF via LibreOffice headless
soffice --headless --convert-to pdf --outdir /tmp/output presentation.pptx

# Step 2: PDF to images via pdf2image (Python)
```

```python
from pdf2image import convert_from_path

def render_slides_to_images(pdf_path, dpi=150):
    """Convert PDF pages to PIL Images."""
    images = convert_from_path(
        pdf_path,
        dpi=dpi,
        fmt='png',
        thread_count=4,
    )
    return images  # List of PIL Image objects
```

**Requirements:**
- LibreOffice (install `libreoffice-nogui` for headless-only)
- Poppler utilities (for pdf2image)
- Python packages: `pdf2image`, `Pillow`

**Caveats:**
- LibreOffice rendering may differ slightly from PowerPoint rendering
- Some animations and transitions are not rendered
- Font substitution may occur if fonts are not embedded

**Source:** [Ask LibreOffice](https://ask.libreoffice.org/t/using-the-headless-command-line-tool-soffice-to-convert-from-powerpoint-to-pdf/13374), [pdf2image (PyPI)](https://pypi.org/project/pdf2image/), [jdhao.github.io](https://jdhao.github.io/2020/03/30/pptx_to_image/)

---

## 6. QA Pipeline Design

### Architecture Overview

```
Input: generated .pptx file
         │
         ▼
┌─────────────────────────┐
│  Step 1: Structural QA  │  Parse PPTX with python-pptx
│  (fast, no rendering)   │  Check: font sizes, margins, word counts,
│                         │  bullet counts, placeholders, colours,
│                         │  slide count, branding, font families
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Step 2: Visual QA      │  Render to images via LibreOffice headless
│  (requires rendering)   │  Check: contrast, overlap, alignment,
│                         │  image quality (BRISQUE), blockiness,
│                         │  visual regression vs golden reference
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Step 3: Cross-Slide    │  Analyse patterns across all slides
│  Consistency Checks     │  Check: font usage consistency, colour
│                         │  palette, heading sizes, bullet styles,
│                         │  consecutive bullet slides, branding
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Step 4: Report         │  Generate QA report with per-slide
│  Generation             │  findings, severity levels, and
│                         │  fix suggestions
└─────────────────────────┘
             │
             ▼
Output: QA Report (JSON/Markdown)
        + optionally corrected .pptx
```

### Step 1: Structural QA (Fast Path)

Parses the PPTX using python-pptx without rendering. Runs in < 1 second for most decks.

**Checks performed:**
- AP-01: Wall of Text (word count per textbox and slide)
- AP-02: Font Size Below Minimum
- AP-03: Too Many Font Families
- AP-04: Inconsistent Bullet Styles
- AP-05: Orphan/Widow Lines
- AP-06: Elements Outside Safe Margins
- AP-09: Missing Speaker Notes
- AP-10: Slide Count vs Duration Mismatch
- AP-11: Placeholder Residue
- AP-13: Image Aspect Ratio Distortion
- AP-14: Too Many Bullet Points
- AP-16: Missing Title Slide
- AP-17: Missing Closing/CTA Slide
- AP-19: Text Overflow/Clipping
- AP-21: Excessive Animations
- AP-24: Dead/Empty Slides

### Step 2: Visual QA (Rendering Required)

Renders slides to images via LibreOffice headless, then applies image analysis.

**Checks performed:**
- AP-07: Low Contrast Text-on-Background (pixel-level analysis)
- AP-12: Image Resolution for Placement Size
- AP-20: Element Overlap (visual confirmation)
- AP-22: Poor Data-Ink Ratio (chart analysis)
- Image quality (BRISQUE scoring)
- Compression artifact detection
- Upscaling detection

### Step 3: Cross-Slide Consistency

Analyses patterns across the full deck.

**Checks performed:**
- AP-03: Font Family Count (deck-wide)
- AP-04: Bullet Style Consistency (deck-wide)
- AP-08: Clashing Colours (palette analysis)
- AP-15: Consecutive Bullet-Heavy Slides
- AP-18: Inconsistent Heading Sizes
- AP-23: Logos/Branding Consistency
- AP-25: Colourblind Safety (palette analysis)
- Colour palette adherence

### Step 4: Report Generation

**Output format (JSON):**
```json
{
  "summary": {
    "total_slides": 15,
    "errors": 3,
    "warnings": 7,
    "info": 2,
    "pass": true
  },
  "slides": [
    {
      "slide_number": 1,
      "issues": [
        {
          "rule": "AP-02",
          "severity": "error",
          "message": "Font size 14pt below minimum 18pt",
          "shape_name": "TextBox 3",
          "fix": "Increase font size to at least 18pt"
        }
      ]
    }
  ],
  "deck_level_issues": [
    {
      "rule": "AP-03",
      "severity": "warning",
      "message": "Deck uses 4 font families (max 2)"
    }
  ]
}
```

### Configuration Schema

```python
QA_CONFIG = {
    # Thresholds (all configurable)
    'max_words_per_textbox': 40,
    'max_words_per_slide': 75,
    'min_font_size_body_pt': 18,
    'min_font_size_title_pt': 24,
    'max_font_families': 2,
    'safe_margin_pct': 0.05,         # 5% action safe
    'title_safe_margin_pct': 0.10,   # 10% title safe
    'min_contrast_ratio': 7.0,       # WCAG AAA for projection
    'max_bullets_per_slide': 6,
    'max_consecutive_bullet_slides': 3,
    'min_speaker_notes_pct': 0.5,    # 50% of content slides
    'slides_per_minute_min': 0.5,
    'slides_per_minute_max': 2.0,
    'brisque_threshold_feature': 35,
    'brisque_threshold_thumbnail': 45,
    'min_image_dpi_equiv': 96,
    'max_aspect_distortion_pct': 5.0,
    'max_overlap_pct': 25,
    'max_transition_types': 2,
    'colourblind_min_distance': 30,

    # Pass/fail criteria
    'fail_on_error': True,           # Any error = fail
    'max_warnings_before_fail': 10,  # > 10 warnings = fail
}
```

---

## 7. Sources

### Presentation Design & Anti-Patterns
- [Presentation Magazine: How many words per slide](https://www.presentationmagazine.com/how-many-words-should-i-have-on-each-slide-18345.htm)
- [ShapeChef: How many words per slide](https://www.shapechef.com/blog/how-many-words-per-slide)
- [Microsoft: 10-20-30 Rule](https://www.microsoft.com/en-us/microsoft-365-life-hacks/presentations/10-20-30-rule-of-powerpoint)
- [Storytelling with Data: Word count](https://www.storytellingwithdata.com/blog/how-many-words-is-too-many)
- [BrightCarbon: Presentation font size](https://www.brightcarbon.com/blog/presentation-font-size/)
- [Beautiful.ai: Font size guide](https://www.beautiful.ai/blog/what-font-size-is-best-for-presentations)
- [AutoPPT: Minimum font size](https://autoppt.com/blog/powerpoint-minimum-font-size-best-practices/)
- [CrappyPresentations: 10 mistakes](https://www.crappypresentations.com/presentation-tips-and-tricks/10-presentation-mistakes)
- [Visme: Bullet points](https://visme.co/blog/bullet-points-presentation/)
- [Ethos3: Why bullets kill presentations](https://ethos3.com/why-bullet-points-kill-presentations/)
- [Rekarda: Animation best practices](https://www.rekarda.com/blog/mastering-powerpoint-animation-best-practices-tips-and-common-pitfalls)
- [Slidor: Best fonts for presentations](https://www.slidor.agency/blog/best-fonts-powerpoint-presentations-designers-guide)
- [Twistly: Rule of Seven](https://twistly.ai/the-rule-of-seven-optimal-slide-content-for-maximum-retention/)
- [SlidesAI: 5-5-5 Rule](https://www.slidesai.io/blog/the-5-5-5-rule-powerpoint)
- [InnerDrive: PowerPoint attention tracking](https://www.innerdrive.co.uk/blog/tracking-powerpoint-attention/)
- [Storyfiner: Slide count for 10 minutes](https://storyfiner.com/the-perfect-slide-count-how-many-slides-for-a-10-minute-presentation/)

### WCAG & Contrast
- [W3C WCAG 2.1: Contrast Minimum (1.4.3)](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [W3C: G17 Technique (7:1 contrast)](https://www.w3.org/WAI/WCAG21/Techniques/general/G17.html)
- [WebAIM: Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [ADG: How to calculate contrast](https://www.accessibility-developer-guide.com/knowledge/colours-and-contrast/how-to-calculate/)
- [Microsoft: Combining colours in PowerPoint](https://support.microsoft.com/en-us/office/combining-colors-in-powerpoint-mistakes-to-avoid-555e1689-85a7-4b2e-aa89-db5270528852)
- [Vanderbilt: Optimising colours for projection](https://edgeforscholars.vumc.org/optimizing-colors-for-projected-presentations/)
- [Think Outside The Slide: Display problems](https://www.thinkoutsidetheslide.com/five-common-problems-with-poor-display-of-powerpoint-presentations/)

### AV Specifications
- [Cinebox: Safe areas](https://www.cinebox.co/help/safeArea)
- [Wikipedia: Safe area (television)](https://en.wikipedia.org/wiki/Safe_area_(television))
- [BenQ: Projector specs explained](https://www.benq.com/en-ap/knowledge-center/knowledge/projector-specs-explained.html)
- [ViewSonic: Lumens guide](https://www.viewsonic.com/library/tech/what-are-lumens-and-how-to-use-them-to-choose-a-projector/)
- [SPIE: Oral presentation guidelines](https://lux.spie.org/conferences-and-exhibitions/optifab/presenters/prepare-to-present/oral-presentation-guidelines)
- [ARL: PowerPoint accessibility guidelines](https://www.arl.org/accessibility-guidelines-for-powerpoint-presentations/)
- [Neuxpower: Font embedding](https://support.neuxpower.com/hc/en-us/articles/360007786978-Embed-subset-or-remove-embedded-fonts-in-PowerPoint-or-Word)

### Image Quality
- [MATLAB: BRISQUE documentation](https://www.mathworks.com/help/images/ref/brisque.html)
- [LearnOpenCV: BRISQUE tutorial](https://learnopencv.com/image-quality-assessment-brisque/)
- [OpenCV: QualityBRISQUE](https://docs.opencv.org/4.x/d8/d99/classcv_1_1quality_1_1QualityBRISQUE.html)
- [Mittal et al.: BRISQUE paper (UT Austin)](https://live.ece.utexas.edu/publications/2012/TIP%20BRISQUE.pdf)
- [BrightCarbon: Picture size and resolution](https://www.brightcarbon.com/blog/powerpoint-picture-size-and-resolution/)
- [Wikipedia: Compression artifact](https://en.wikipedia.org/wiki/Compression_artifact)
- [IEEE: Block boundary discontinuity](https://ieeexplore.ieee.org/document/678634/)

### Visual Regression Testing
- [Pixelmatch (npm)](https://www.npmjs.com/package/pixelmatch)
- [jest-image-snapshot (GitHub)](https://github.com/americanexpress/jest-image-snapshot)
- [Perceptual hashing (Wikipedia)](https://en.wikipedia.org/wiki/Perceptual_hashing)
- [pHash.org thesis](https://www.phash.org/docs/pubs/thesis_zauner.pdf)
- [Cloudinary: pHash guide](https://cloudinary.com/blog/how_to_automatically_identify_similar_images_using_phash)
- [pdf2image (PyPI)](https://pypi.org/project/pdf2image/)
- [Ask LibreOffice: Headless conversion](https://ask.libreoffice.org/t/using-the-headless-command-line-tool-soffice-to-convert-from-powerpoint-to-pdf/13374)

### Colour Accessibility
- [David Mathlogic: Colouring for colourblindness](https://davidmathlogic.com/colorblind/)
- [Visme: Colour blind friendly palette](https://visme.co/blog/color-blind-friendly-palette/)
- [BCGSC: Colourblind palettes](https://mk.bcgsc.ca/colorblind/palettes.mhtml)
- [Colorblindcheck R package](https://jakubnowosad.com/colorblindcheck/)
- [Canva: Colour wheel](https://www.canva.com/colors/color-wheel/)

### python-pptx Technical Reference
- [python-pptx: Shape position and size](https://python-pptx.readthedocs.io/en/latest/dev/analysis/shp-pos-and-size.html)
- [python-pptx: Text objects](https://python-pptx.readthedocs.io/en/latest/api/text.html)
- [python-pptx: AutoShapes](https://python-pptx.readthedocs.io/en/latest/user/autoshapes.html)
- [python-pptx: Slides](https://python-pptx.readthedocs.io/en/latest/user/slides.html)
- [python-pptx: Text auto-fit](https://python-pptx.readthedocs.io/en/latest/dev/analysis/txt-autofit-text.html)
- [PptxGenJS: Text API](https://gitbrent.github.io/PptxGenJS/docs/api-text.html)

### Typography
- [Fontfabric: Orphan typography](https://www.fontfabric.com/blog/orphan-typography/)
- [Butterick: Widow and orphan control](https://practicaltypography.com/widow-and-orphan-control.html)
- [Hanjing (Medium): Font sizing best practices](https://hanjing.medium.com/font-sizing-4259801c04c1)
- [Columbia: Headings visual identity](https://visualidentity.columbia.edu/content/headings)

### Data Visualisation
- [The Doublethink: Tufte's principles](https://thedoublethink.com/tuftes-principles-for-visualizing-quantitative-information/)
- [Holistics: Data-ink ratio](https://www.holistics.io/blog/data-ink-ratio/)
- [Nolan Haims: Data-ink and chart junk](https://www.nolanhaimscreative.com/blog/2012315data-ink-and-the-dangers-of-chart-junk-in-information-design-html-2-yenlf)
