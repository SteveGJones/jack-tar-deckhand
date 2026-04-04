"""SmartArt renderer — dispatches to Mermaid CLI, Vega-Lite CLI, custom SVG, or Matplotlib.

Handles the comparator pattern and builds SmartArtManifest entries.
"""

import hashlib
import json
import os
import re
import subprocess
import uuid

from src.smartart_svg import render_custom_svg
from src.render_chart import render_chart


# ---------------------------------------------------------------------------
# SVG post-processing and rasterisation helpers
# ---------------------------------------------------------------------------

def _postprocess_mermaid_svg(svg_path):
    """Set explicit width/height pixel attributes from viewBox.

    Mermaid CLI emits ``width="100%"`` which PowerPoint cannot use.  This
    function reads the viewBox dimensions and writes them back as explicit
    pixel values so downstream rasterisers and assemblers get a concrete size.
    """
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg = f.read()
    vb_match = re.search(r'viewBox="[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)"', svg)
    if vb_match:
        w = int(float(vb_match.group(1)))
        h = int(float(vb_match.group(2)))
        svg = re.sub(r'width="[^"]*"', f'width="{w}"', svg, count=1)
        if 'height="' in svg:
            svg = re.sub(r'height="[^"]*"', f'height="{h}"', svg, count=1)
        else:
            svg = svg.replace(f'width="{w}"', f'width="{w}" height="{h}"', 1)
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg)


def _rasterise_svg_to_png(svg_path, png_path, width=1600, height=900):
    """Convert SVG to PNG.

    Tries in order:
    1. cairosvg (Python, highest fidelity)
    2. Node.js sharp via subprocess
    3. Pillow placeholder (last resort — blank transparent image)
    """
    try:
        import cairosvg
        cairosvg.svg2png(url=svg_path, write_to=png_path,
                         output_width=width, output_height=height)
        return
    except ImportError:
        pass

    try:
        result = subprocess.run(
            ['node', '-e',
             f'const sharp = require("sharp"); '
             f'sharp("{svg_path}")'
             f'.resize({width}, {height}, {{ fit: "contain", background: {{ r:255,g:255,b:255,alpha:0 }} }})'
             f'.png().toFile("{png_path}")'
             f'.then(() => console.log("OK"))'
             f'.catch(e => {{ console.error(e.message); process.exit(1); }});'],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and os.path.exists(png_path):
            return
    except Exception:
        pass

    # Last resort: Pillow placeholder (transparent image)
    from PIL import Image as PILImage
    img = PILImage.new('RGBA', (width, height), (255, 255, 255, 0))
    img.save(png_path)


# ---------------------------------------------------------------------------
# Engine implementations
# ---------------------------------------------------------------------------

def render_custom_svg_engine(spec, style_guide, output_dir):
    """Render a custom SVG spec and save to a file.

    Args:
        spec: SmartArt spec dict (must include 'graphic_type' and 'data').
        style_guide: StyleGuide dict.
        output_dir: Directory to write the SVG file.

    Returns:
        Absolute path to the saved .svg file.
    """
    svg_string = render_custom_svg(spec, style_guide)
    filename = f"smartart-{spec.get('graphic_type', 'graphic')}-{uuid.uuid4().hex[:8]}.svg"
    svg_path = os.path.join(output_dir, filename)
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_string)
    return svg_path


def render_mermaid(spec, style_guide, output_dir):
    """Render a Mermaid diagram using the Mermaid CLI (mmdc via npx).

    Injects brand theme variables before running the CLI.  The SVG output is
    post-processed to embed explicit pixel dimensions from its viewBox, then
    rasterised to PNG.  The SVG source is kept alongside the PNG for debugging
    and re-rendering.

    Args:
        spec: SmartArt spec dict; spec['data']['syntax'] must contain Mermaid syntax.
        style_guide: StyleGuide dict.
        output_dir: Directory to write output files.

    Returns:
        Absolute path to the rasterised .png file.

    Raises:
        RuntimeError: If the Mermaid CLI returns a non-zero exit code.
    """
    syntax = spec['data']['syntax']
    palette = style_guide.get('palette', {})

    # Build Mermaid theme directive with brand colours
    theme_vars = {
        'primaryColor': '#' + palette.get('primary', '1a73e8'),
        'primaryTextColor': '#' + palette.get('text_primary', '1a1a1a'),
        'lineColor': '#' + palette.get('text_primary', '666666'),
        'fontFamily': style_guide.get('typography', {}).get('body_font', 'sans-serif'),
    }
    theme_directive = (
        f"%%{{init: {{'theme': 'base', 'themeVariables': {json.dumps(theme_vars)}}}}}%%\n"
    )
    full_syntax = theme_directive + syntax

    # Write .mmd source file
    run_id = uuid.uuid4().hex[:8]
    mmd_path = os.path.join(output_dir, f'input-{run_id}.mmd')
    svg_path = os.path.join(output_dir, f'output-{run_id}.svg')
    png_path = os.path.join(output_dir, f'output-{run_id}.png')
    with open(mmd_path, 'w', encoding='utf-8') as f:
        f.write(full_syntax)

    result = subprocess.run(
        ['npx', 'mmdc', '-i', mmd_path, '-o', svg_path,
         '-b', 'transparent', '--width', '1600'],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Mermaid CLI failed: {result.stderr}")

    # Post-process SVG: replace width="100%" with explicit pixel dimensions
    _postprocess_mermaid_svg(svg_path)

    # Rasterise SVG → PNG (mandatory — PowerPoint can't render SVG <foreignObject>)
    _rasterise_svg_to_png(svg_path, png_path)

    return png_path


def render_vega_lite(spec, style_guide, output_dir):
    """Render a Vega-Lite spec using the vl2svg CLI (via npx).

    Injects brand style config into the spec before running the CLI.

    Args:
        spec: SmartArt spec dict; spec['data']['spec'] must contain a Vega-Lite spec.
        style_guide: StyleGuide dict.
        output_dir: Directory to write output files.

    Returns:
        Absolute path to the generated .svg file.

    Raises:
        RuntimeError: If the Vega-Lite CLI returns a non-zero exit code.
    """
    vl_spec = spec['data']['spec'].copy()

    # Inject 16:9 dimensions — prevents portrait-oriented default
    vl_spec['width'] = 1600
    vl_spec['height'] = 900
    vl_spec['autosize'] = {'type': 'fit', 'contains': 'padding'}

    # Inject brand style into Vega-Lite config
    palette = style_guide.get('palette', {})
    vl_spec.setdefault('config', {})
    vl_spec['config']['background'] = '#' + palette.get('background', 'ffffff')
    vl_spec['config']['font'] = style_guide.get('typography', {}).get('body_font', 'sans-serif')

    # Inject chart series colours if available
    chart_series = palette.get('chart_series', [])
    if chart_series:
        vl_spec['config'].setdefault('range', {})
        vl_spec['config']['range']['category'] = ['#' + c for c in chart_series]

    run_id = uuid.uuid4().hex[:8]
    spec_path = os.path.join(output_dir, f'vl-spec-{run_id}.json')
    svg_path = os.path.join(output_dir, f'vl-output-{run_id}.svg')
    with open(spec_path, 'w', encoding='utf-8') as f:
        json.dump(vl_spec, f)

    result = subprocess.run(
        ['npx', 'vl2svg', spec_path, svg_path],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Vega-Lite CLI failed: {result.stderr}")

    return svg_path


def render_matplotlib(spec, style_guide, output_dir):
    """Render a chart using Matplotlib via the existing render_chart() helper.

    Args:
        spec: SmartArt spec dict; spec['data'] must be a chart data dict with
              'chart_type' and chart-specific keys.
        style_guide: StyleGuide dict.
        output_dir: Directory to write the PNG.

    Returns:
        Absolute path to the generated .png file.
    """
    data = spec.get('data', {})
    chart_type = data.get('chart_type', 'bar')
    run_id = uuid.uuid4().hex[:8]
    output_path = os.path.join(output_dir, f'chart-{run_id}.png')
    render_chart(
        chart_type=chart_type,
        data=data,
        output_path=output_path,
        style_guide=style_guide,
    )
    return output_path


# ---------------------------------------------------------------------------
# Manifest entry builder
# ---------------------------------------------------------------------------

def build_manifest_entry(
    slide_number,
    graphic_type,
    engine,
    enrichment_tier,
    file_path,
    svg_path,
    dimensions,
    alt_text,
    node_count=0,
    status='rendered',
    comparator_results=None,
    content_hash=None,
):
    """Build a SmartArtManifest per-graphic entry dict.

    Args:
        slide_number: Integer slide number (1-based).
        graphic_type: SmartArt graphic type string (e.g. 'flowchart', 'swot').
        engine: Engine used (e.g. 'mermaid', 'custom_svg').
        enrichment_tier: One of the enrichment tier enum values.
        file_path: Path to the primary output file (PNG or SVG).
        svg_path: Path to the SVG source file (may equal file_path for SVG engines).
        dimensions: Dict with 'width' and 'height' keys.
        alt_text: Accessibility alt-text string.
        node_count: Number of nodes/elements in the graphic (default 0).
        status: One of 'rendered', 'compared', 'enriched', 'failed'.
        comparator_results: Optional comparator results dict.
        content_hash: Optional pre-computed content hash string.

    Returns:
        Dict matching the SmartArtManifest per-graphic schema.
    """
    smartart_id = f"sa-slide-{slide_number}-{graphic_type}"

    if content_hash is None:
        # Derive a stable hash from the file path so it's deterministic per file
        content_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]

    entry = {
        'smartart_id': smartart_id,
        'slide_number': slide_number,
        'graphic_type': graphic_type,
        'engine_used': engine,
        'enrichment_tier': enrichment_tier,
        'file_path': file_path,
        'svg_source_path': svg_path,
        'status': status,
        'dimensions': dimensions,
        'node_count': node_count,
        'alt_text': alt_text,
        'content_hash': content_hash,
    }

    if comparator_results is not None:
        entry['comparator_results'] = comparator_results

    return entry


# ---------------------------------------------------------------------------
# Top-level render dispatcher
# ---------------------------------------------------------------------------

_ENGINE_DISPATCH = {
    'custom_svg': render_custom_svg_engine,
    'mermaid': render_mermaid,
    'vega_lite': render_vega_lite,
    'matplotlib': render_matplotlib,
}


def render(spec, style_guide, phase, output_dir):
    """Dispatch rendering to the correct engine and return a manifest entry.

    Handles the comparator pattern: if spec['comparator_engines'] is non-empty,
    renders each candidate engine and records results.  Errors are caught
    gracefully — the entry status is set to 'failed' rather than propagating
    the exception.

    Args:
        spec: SmartArt spec dict.  Must include:
            - 'slide_number' (int)
            - 'graphic_type' (str)
            - 'engine' (str) — primary engine
            - 'enrichment_tier' (str)
            - 'data' (dict) — engine-specific data
            - 'comparator_engines' (list[str]) — additional engines to compare
        style_guide: StyleGuide dict.
        phase: Rendering phase string ('draft' or 'production').
        output_dir: Directory to write output files.

    Returns:
        Dict matching the SmartArtManifest per-graphic schema.
    """
    slide_number = spec['slide_number']
    graphic_type = spec['graphic_type']
    primary_engine = spec['engine']
    enrichment_tier = spec.get('enrichment_tier', 'pure_programmatic')
    comparator_engines = spec.get('comparator_engines', [])

    alt_text = spec.get('alt_text', f"{graphic_type} diagram")
    dimensions = spec.get('dimensions', {'width': 1920, 'height': 1080})

    dispatch_fn = _ENGINE_DISPATCH.get(primary_engine)
    if dispatch_fn is None:
        return build_manifest_entry(
            slide_number=slide_number,
            graphic_type=graphic_type,
            engine=primary_engine,
            enrichment_tier=enrichment_tier,
            file_path='',
            svg_path='',
            dimensions=dimensions,
            alt_text=alt_text,
            status='failed',
        )

    # Render primary engine
    try:
        primary_path = dispatch_fn(spec, style_guide, output_dir)
        # mermaid returns PNG; SVG source lives at the same stem
        if primary_engine == 'mermaid':
            file_path = primary_path  # PNG
            svg_path = primary_path.replace('.png', '.svg')
            if not os.path.exists(svg_path):
                svg_path = primary_path
        # matplotlib primary output is PNG (no SVG source)
        elif primary_engine == 'matplotlib':
            file_path = primary_path
            svg_path = ''
        else:
            file_path = primary_path
            svg_path = primary_path
        primary_status = 'rendered'
    except Exception as exc:  # noqa: BLE001
        return build_manifest_entry(
            slide_number=slide_number,
            graphic_type=graphic_type,
            engine=primary_engine,
            enrichment_tier=enrichment_tier,
            file_path='',
            svg_path='',
            dimensions=dimensions,
            alt_text=alt_text,
            status='failed',
        )

    # Handle comparator pattern
    if comparator_engines:
        candidates = [{'engine': primary_engine, 'score': 0.0, 'file_path': primary_path}]
        for comp_engine in comparator_engines:
            comp_fn = _ENGINE_DISPATCH.get(comp_engine)
            if comp_fn is None:
                continue
            try:
                comp_path = comp_fn(spec, style_guide, output_dir)
                candidates.append({'engine': comp_engine, 'score': 0.0, 'file_path': comp_path})
            except Exception:  # noqa: BLE001
                pass

        comparator_results = {
            'candidates': candidates,
            'winner': primary_engine,
            'phase': phase,
        }
        return build_manifest_entry(
            slide_number=slide_number,
            graphic_type=graphic_type,
            engine=primary_engine,
            enrichment_tier=enrichment_tier,
            file_path=file_path,
            svg_path=svg_path,
            dimensions=dimensions,
            alt_text=alt_text,
            status='compared',
            comparator_results=comparator_results,
        )

    return build_manifest_entry(
        slide_number=slide_number,
        graphic_type=graphic_type,
        engine=primary_engine,
        enrichment_tier=enrichment_tier,
        file_path=file_path,
        svg_path=svg_path,
        dimensions=dimensions,
        alt_text=alt_text,
        status=primary_status,
    )
