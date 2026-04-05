"""SmartArt data extractor — transforms slide body_points into engine-specific structured data.

Deterministic transformation only. No LLM calls.
"""

import re
from src.smartart_svg.tokens import extract_style_tokens

# ---------------------------------------------------------------------------
# Node ID generation helpers
# ---------------------------------------------------------------------------

_NODE_ID_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _node_id(index):
    """Generate Mermaid-safe node ID: A-Z, then AA, AB, ..."""
    if index < 26:
        return _NODE_ID_CHARS[index]
    first = _NODE_ID_CHARS[(index // 26) - 1]
    second = _NODE_ID_CHARS[index % 26]
    return first + second


def _clean_label(text):
    """Strip characters that break Mermaid node labels."""
    # Remove quotes and braces; keep alphanumeric, spaces, punctuation safe for Mermaid
    return re.sub(r'["\[\]{}|]', '', text).strip()


# ---------------------------------------------------------------------------
# Colon-split helper
# ---------------------------------------------------------------------------

def _split_colon(point):
    """Split 'Label: Value' on first colon. Returns (label, value) or (None, point)."""
    if ':' in point:
        label, _, value = point.partition(':')
        return label.strip(), value.strip()
    return None, point.strip()


def _parse_numeric(value):
    """Try int then float; return original string if neither works."""
    try:
        int_val = int(value.replace(',', ''))
        return int_val
    except (ValueError, AttributeError):
        pass
    try:
        return float(value.replace(',', ''))
    except (ValueError, AttributeError):
        pass
    return value


# ---------------------------------------------------------------------------
# 1. extract_graph_data
# ---------------------------------------------------------------------------

def extract_graph_data(body_points, graphic_type):
    """Convert body_points to Mermaid syntax dict.

    Returns:
        dict with keys: engine, syntax, diagram_type, node_count
    """
    if graphic_type == 'gantt':
        return _extract_gantt(body_points)
    elif graphic_type == 'decision_tree':
        return _extract_decision_tree(body_points)
    else:
        # Default: flowchart (sequential)
        return _extract_flowchart(body_points)


def _extract_flowchart(body_points):
    lines = ['graph TD']
    node_ids = []
    for i, point in enumerate(body_points):
        nid = _node_id(i)
        node_ids.append(nid)
        label = _clean_label(point)
        lines.append(f'  {nid}["{label}"]')
    # Connect sequentially
    for i in range(len(node_ids) - 1):
        lines.append(f'  {node_ids[i]} --> {node_ids[i + 1]}')
    syntax = '\n'.join(lines)
    return {
        'engine': 'mermaid',
        'syntax': syntax,
        'diagram_type': 'flowchart',
        'node_count': len(body_points),
    }


def _extract_decision_tree(body_points):
    """Parse decision tree from body_points.

    Heuristic: first point is root question; subsequent points with "Yes:"/"No:"
    or "Yes ..."/"No ..." prefixes become branches. All others treated as
    sequential children of the root.
    """
    lines = ['graph TD']
    nodes = []

    # Root node
    root_label = _clean_label(body_points[0]) if body_points else 'Start'
    root_id = _node_id(0)
    lines.append(f'  {root_id}{{"{root_label}"}}')
    nodes.append(root_id)

    for i, point in enumerate(body_points[1:], start=1):
        nid = _node_id(i)
        label = _clean_label(point)
        # Try "Yes:" or "No:" pattern
        m = re.match(r'^(Yes|No)\s*:\s*(.+)$', point.strip(), re.IGNORECASE)
        if m:
            edge_label = m.group(1)
            node_label = _clean_label(m.group(2))
            lines.append(f'  {nid}["{node_label}"]')
            lines.append(f'  {root_id} -- {edge_label} --> {nid}')
        else:
            lines.append(f'  {nid}["{label}"]')
            lines.append(f'  {nodes[-1]} --> {nid}')
        nodes.append(nid)

    syntax = '\n'.join(lines)
    return {
        'engine': 'mermaid',
        'syntax': syntax,
        'diagram_type': 'decision_tree',
        'node_count': len(body_points),
    }


def _extract_gantt(body_points, inline_data=None):
    """Convert task data to Mermaid gantt syntax.

    Supports two input modes:
    - inline_data: {'tasks': [{'label': str, 'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}, ...]}
    - body_points: 'Task: Start-End' patterns (e.g., 'Research: Jan-Mar')

    Mermaid gantt requires YYYY-MM-DD dateFormat for reliable rendering.
    """
    if inline_data and 'tasks' in inline_data:
        return _gantt_from_inline(inline_data)

    # Parse body_points — try to extract date ranges
    lines = ['gantt', '    dateFormat YYYY-MM-DD', '    section Tasks']
    node_count = 0

    for point in body_points:
        label, value = _split_colon(point)
        if label is None:
            label = point.strip()
            value = ''

        safe_label = label.replace(':', '').strip()
        if not safe_label:
            continue

        # Try to parse date-like ranges: "Q1 2025" "Jan-Mar" "2025-01-01 to 2025-03-31"
        date_range = _parse_date_range(value)
        if date_range:
            start, end = date_range
            task_id = re.sub(r'[^a-zA-Z0-9]', '', safe_label)[:10].lower()
            lines.append(f'    {safe_label} :{task_id}, {start}, {end}')
            node_count += 1
        else:
            # Can't parse dates — use a 30-day duration relative to previous task
            task_id = re.sub(r'[^a-zA-Z0-9]', '', safe_label)[:10].lower()
            lines.append(f'    {safe_label} :{task_id}, 30d')
            node_count += 1

    syntax = '\n'.join(lines)
    return {
        'engine': 'mermaid',
        'syntax': syntax,
        'diagram_type': 'gantt',
        'node_count': node_count,
    }


def _gantt_from_inline(inline_data):
    """Build Mermaid gantt from structured inline_data with explicit dates."""
    tasks = inline_data['tasks']
    title = inline_data.get('title', '')
    section = inline_data.get('section', 'Tasks')

    lines = ['gantt', '    dateFormat YYYY-MM-DD']
    if title:
        lines.append(f'    title {title}')
    lines.append(f'    section {section}')

    for task in tasks:
        label = task['label'].replace(':', '').strip()
        start = task['start']
        end = task['end']
        status = task.get('status', '')
        task_id = re.sub(r'[^a-zA-Z0-9]', '', label)[:10].lower()

        status_prefix = f'{status}, ' if status else ''
        lines.append(f'    {label} :{status_prefix}{task_id}, {start}, {end}')

    syntax = '\n'.join(lines)
    return {
        'engine': 'mermaid',
        'syntax': syntax,
        'diagram_type': 'gantt',
        'node_count': len(tasks),
    }


_QUARTER_TO_DATES = {
    'Q1': ('01-01', '03-31'),
    'Q2': ('04-01', '06-30'),
    'Q3': ('07-01', '09-30'),
    'Q4': ('10-01', '12-31'),
}

_MONTH_TO_NUM = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
}


def _parse_date_range(value):
    """Try to parse a date range string into (start_date, end_date) YYYY-MM-DD.

    Handles: 'Q1 2025 to Q3 2025', 'Jan-Mar', '2025-01-01 to 2025-06-30',
             'Now to Q2 2025', 'Q2 to Q3 2025'
    Returns None if parsing fails.
    """
    if not value:
        return None
    value = value.strip()

    # Try YYYY-MM-DD to YYYY-MM-DD
    iso_match = re.match(r'(\d{4}-\d{2}-\d{2})\s*(?:to|[-–])\s*(\d{4}-\d{2}-\d{2})', value)
    if iso_match:
        return (iso_match.group(1), iso_match.group(2))

    # Try "Q1 2025 to Q3 2025" or "Q1 to Q3 2025" or "Now to Q2 2025"
    q_match = re.match(r'(?:(Q[1-4])\s+(\d{4})|Now)\s*(?:to|[-–])\s*(Q[1-4])\s+(\d{4})', value)
    if q_match:
        if q_match.group(1):
            sq, sy = q_match.group(1), q_match.group(2)
            start = f'{sy}-{_QUARTER_TO_DATES[sq][0]}'
        else:
            start = '2025-01-01'  # "Now" defaults to start of year
        eq, ey = q_match.group(3), q_match.group(4)
        end = f'{ey}-{_QUARTER_TO_DATES[eq][1]}'
        return (start, end)

    # Try "Q2 to Q3 2025" (start quarter implied same year)
    q_match2 = re.match(r'(Q[1-4])\s*(?:to|[-–])\s*(Q[1-4])\s+(\d{4})', value)
    if q_match2:
        sq, eq, year = q_match2.group(1), q_match2.group(2), q_match2.group(3)
        start = f'{year}-{_QUARTER_TO_DATES[sq][0]}'
        end = f'{year}-{_QUARTER_TO_DATES[eq][1]}'
        return (start, end)

    # Try month abbreviation range: "Jan-Mar" or "May-Aug"
    month_match = re.match(r'([A-Za-z]{3})\s*[-–]\s*([A-Za-z]{3})', value)
    if month_match:
        sm = month_match.group(1).lower()[:3]
        em = month_match.group(2).lower()[:3]
        if sm in _MONTH_TO_NUM and em in _MONTH_TO_NUM:
            return (f'2025-{_MONTH_TO_NUM[sm]}-01', f'2025-{_MONTH_TO_NUM[em]}-28')

    return None


# ---------------------------------------------------------------------------
# 2. extract_series_data
# ---------------------------------------------------------------------------

_VEGA_SCHEMA = 'https://vega.github.io/schema/vega-lite/v5.json'

_VEGA_MARK_MAP = {
    'bar_chart': 'bar',
    'line_chart': 'line',
    'radar_chart': 'point',  # closest approximation in Vega-Lite
}


def extract_series_data(body_points, chart_type, engine='vega_lite'):
    """Parse 'Label: Value' body_points into chart data.

    Returns:
        dict with engine-specific chart spec
    """
    labels = []
    values = []
    for point in body_points:
        label, raw_value = _split_colon(point)
        if label is None:
            label = point
            raw_value = '0'
        numeric = _parse_numeric(raw_value)
        labels.append(label)
        values.append(numeric)

    if engine == 'matplotlib':
        return {
            'engine': 'matplotlib',
            'chart_type': chart_type,
            'data': {
                'labels': labels,
                'values': values,
            },
        }

    # Default: vega_lite
    mark = _VEGA_MARK_MAP.get(chart_type, 'bar')
    vega_values = [{'label': l, 'value': v} for l, v in zip(labels, values)]
    spec = {
        '$schema': _VEGA_SCHEMA,
        'mark': mark,
        'data': {'values': vega_values},
        'encoding': {
            'x': {'field': 'label', 'type': 'ordinal'},
            'y': {'field': 'value', 'type': 'quantitative'},
        },
    }
    return {
        'engine': 'vega_lite',
        'chart_type': chart_type,
        'spec': spec,
    }


# ---------------------------------------------------------------------------
# 3. extract_spatial_data
# ---------------------------------------------------------------------------

_SWOT_KEYS = ['Strengths', 'Weaknesses', 'Opportunities', 'Threats']
_MAX_SWOT_ITEMS = 5


def extract_spatial_data(body_points, graphic_type):
    """Convert body_points to custom_svg structured data.

    Returns:
        dict with keys: engine, graphic_type, data
    """
    dispatchers = {
        'swot': _extract_swot,
        'timeline': _extract_timeline,
        'pipeline_funnel': _extract_pipeline_funnel,
        'venn': _extract_venn,
        'feature_matrix': _extract_feature_matrix,
    }
    extractor = dispatchers.get(graphic_type, _extract_generic_spatial)
    data = extractor(body_points)
    return {
        'engine': 'custom_svg',
        'graphic_type': graphic_type,
        'data': data,
    }


def _extract_swot(body_points):
    """Parse SWOT quadrants from body_points.

    Matches "Strengths:", "Weaknesses:", "Opportunities:", "Threats:" prefixes
    (case-insensitive). Items within each quadrant are comma-separated.
    Truncates to MAX_SWOT_ITEMS per quadrant.
    """
    quadrant_map = {k.lower(): {'label': k, 'items': []} for k in _SWOT_KEYS}

    for point in body_points:
        label, value = _split_colon(point)
        if label is None:
            continue
        key = label.strip().lower()
        if key in quadrant_map:
            raw_items = [item.strip() for item in value.split(',') if item.strip()]
            quadrant_map[key]['items'] = raw_items[:_MAX_SWOT_ITEMS]

    quadrants = [quadrant_map[k.lower()] for k in _SWOT_KEYS]
    return {'quadrants': quadrants}


def _extract_timeline(body_points):
    """Parse 'Label: Description' into timeline stages."""
    stages = []
    for point in body_points:
        label, description = _split_colon(point)
        if label is None:
            label = point
            description = ''
        stages.append({'label': label, 'description': description})
    return {'stages': stages}


def _extract_pipeline_funnel(body_points):
    """Parse 'Stage: Value' into funnel stages with numeric values."""
    stages = []
    for point in body_points:
        label, raw_value = _split_colon(point)
        if label is None:
            label = point
            raw_value = '0'
        numeric = _parse_numeric(raw_value)
        stages.append({'label': label, 'value': numeric})
    return {'stages': stages}


def _extract_venn(body_points):
    """Parse 'Set A: item1, item2' patterns into Venn set definitions."""
    sets = []
    shared = []
    for point in body_points:
        label, value = _split_colon(point)
        if label is None:
            continue
        items = [item.strip() for item in value.split(',') if item.strip()]
        if label.strip().lower() == 'shared':
            shared = items
        else:
            sets.append({'label': label.strip(), 'items': items})
    return {'sets': sets, 'shared': shared}


def _extract_feature_matrix(body_points):
    """Parse feature matrix from structured body_points.

    Expects first point to be 'Features: col1, col2, ...' and subsequent
    points to be 'Row label: val1, val2, ...'.
    """
    if not body_points:
        return {'columns': [], 'rows': []}

    # First point defines columns
    first_label, first_value = _split_colon(body_points[0])
    if first_label is None:
        return {'columns': [], 'rows': []}

    columns = [col.strip() for col in first_value.split(',') if col.strip()]
    rows = []
    for point in body_points[1:]:
        row_label, row_value = _split_colon(point)
        if row_label is None:
            continue
        cell_values = [v.strip() for v in row_value.split(',') if v.strip()]
        rows.append({'label': row_label.strip(), 'values': cell_values})

    return {'columns': columns, 'rows': rows}


def _extract_generic_spatial(body_points):
    """Fallback: convert body_points to a simple items list."""
    items = []
    for point in body_points:
        label, value = _split_colon(point)
        if label:
            items.append({'label': label, 'value': value})
        else:
            items.append({'label': point, 'value': ''})
    return {'items': items}


# ---------------------------------------------------------------------------
# 4. extract (dispatcher)
# ---------------------------------------------------------------------------

_MERMAID_GRAPHIC_TYPES = {'flowchart', 'decision_tree', 'gantt'}
_VEGA_GRAPHIC_TYPES = {'bar_chart', 'line_chart', 'radar_chart'}
_SPATIAL_GRAPHIC_TYPES = {'swot', 'timeline', 'pipeline_funnel', 'feature_matrix', 'venn'}


def _build_vega_from_inline(inline_data, graphic_type, engine='vega_lite'):
    """Build a Vega-Lite spec from structured inline_data."""
    series = inline_data.get('series', [])
    values = [{'label': item['label'], 'value': item['value']} for item in series]

    mark = 'bar'
    if graphic_type == 'line_chart':
        mark = 'line'
    elif graphic_type == 'radar_chart':
        mark = 'point'

    spec = {
        '$schema': 'https://vega.github.io/schema/vega-lite/v5.json',
        'mark': mark,
        'data': {'values': values},
        'encoding': {
            'x': {'field': 'label', 'type': 'ordinal'},
            'y': {'field': 'value', 'type': 'quantitative'}
        }
    }
    return {
        'engine': engine,
        'chart_type': graphic_type,
        'spec': spec
    }


def _build_matplotlib_from_inline(inline_data, graphic_type):
    """Build Matplotlib data dict from structured inline_data."""
    series = inline_data.get('series', [])
    return {
        'engine': 'matplotlib',
        'chart_type': graphic_type.replace('_chart', ''),
        'data': {
            'labels': [item['label'] for item in series],
            'values': [item['value'] for item in series]
        }
    }


def extract(slide, selection, style_guide):
    """Top-level extractor — dispatches to the right sub-extractor.

    Args:
        slide: dict with slide_number, headline, body_points
        selection: dict with slide_number, graphic_type, enrichment_tier, engine
        style_guide: StyleGuide dict (palette, typography)

    Returns:
        SmartArtSpec entry dict (matches per-spec item in schema)
    """
    body_points = slide.get('body_points', [])
    inline_data = slide.get('data', {}).get('inline_data')
    graphic_type = selection['graphic_type']
    engine = selection['engine']
    overflow_applied = 'none'

    # Prefer inline_data when present — structured data that bypasses regex parsing
    # IMPORTANT: check explicit engine first, not graphic_type membership,
    # because a graphic_type like radar_chart can be routed to custom_svg
    if inline_data is not None:
        if engine == 'custom_svg':
            # Pass inline_data through directly — custom SVG layouts read it as-is
            extracted_data = {'engine': engine, 'graphic_type': graphic_type, 'data': inline_data}
        elif engine == 'vega_lite':
            extracted_data = _build_vega_from_inline(inline_data, graphic_type, engine)
        elif engine == 'matplotlib':
            extracted_data = _build_matplotlib_from_inline(inline_data, graphic_type)
        elif graphic_type == 'gantt':
            extracted_data = _extract_gantt(body_points, inline_data=inline_data)
        elif graphic_type in _VEGA_GRAPHIC_TYPES:
            extracted_data = _build_vega_from_inline(inline_data, graphic_type, engine)
        else:
            # For other engines, inline_data is passed through as-is
            extracted_data = {'engine': engine, 'graphic_type': graphic_type, 'data': inline_data}
    elif engine == 'mermaid' or graphic_type in _MERMAID_GRAPHIC_TYPES:
        extracted_data = extract_graph_data(body_points, graphic_type)
    elif engine == 'vega_lite' or engine == 'matplotlib' or graphic_type in _VEGA_GRAPHIC_TYPES:
        extracted_data = extract_series_data(body_points, graphic_type, engine=engine)
    elif engine == 'custom_svg' or graphic_type in _SPATIAL_GRAPHIC_TYPES:
        extracted_data = extract_spatial_data(body_points, graphic_type)
        # Detect overflow from SWOT truncation
        if graphic_type == 'swot':
            for quadrant in extracted_data.get('data', {}).get('quadrants', []):
                # We stored items at max 5; check if any were truncated by counting
                # We can't know the original count here, so rely on caller context.
                # Instead, check by re-parsing to compare — simpler: track in data itself.
                pass
    else:
        extracted_data = {'engine': engine, 'graphic_type': graphic_type, 'items': body_points}

    # Normalise: extracted_data may be the full spatial dict or just the inner data dict
    # For custom_svg, extract_spatial_data returns {'engine':..,'graphic_type':..,'data':{..}}
    # For others, the sub-functions return a flat dict that IS the data.
    if engine == 'custom_svg' or graphic_type in _SPATIAL_GRAPHIC_TYPES:
        data_payload = extracted_data.get('data', extracted_data)
    else:
        data_payload = extracted_data

    # Detect overflow: check SWOT before we truncated vs after (simple length heuristic)
    if graphic_type == 'swot':
        for point in body_points:
            label, value = _split_colon(point)
            if label and label.strip().lower() in [k.lower() for k in _SWOT_KEYS]:
                items = [i.strip() for i in value.split(',') if i.strip()]
                if len(items) > _MAX_SWOT_ITEMS:
                    overflow_applied = 'truncate'
                    break

    valid, errors = validate_spec({
        'engine': engine,
        'data': data_payload,
        'graphic_type': graphic_type,
    })

    style_tokens = extract_style_tokens(style_guide)

    return {
        'slide_number': selection['slide_number'],
        'graphic_type': graphic_type,
        'engine': engine,
        'enrichment_tier': selection['enrichment_tier'],
        'data': data_payload,
        'overflow_applied': overflow_applied,
        'style_tokens': style_tokens,
        'validation_status': 'valid' if valid else 'invalid',
        'comparator_engines': [],
    }


# ---------------------------------------------------------------------------
# 5. validate_spec
# ---------------------------------------------------------------------------

_ENGINE_REQUIRED_KEYS = {
    'mermaid': ['syntax'],
    'vega_lite': ['$schema', 'mark', 'data', 'encoding'],
    'matplotlib': ['chart_type', 'data'],
    'custom_svg': [],  # flexible — no universal required key beyond engine
}

# For validate_spec the caller passes the outer spec with 'data' as a sub-dict.
# Engine-specific required keys are checked inside spec['data'].

def validate_spec(spec):
    """Validate a spec entry dict.

    Args:
        spec: dict with at least 'engine', 'data', 'graphic_type'

    Returns:
        (bool valid, list[str] errors)
    """
    errors = []
    engine = spec.get('engine')
    data = spec.get('data', {})

    if engine is None:
        errors.append("Missing 'engine' key")
        return False, errors

    required_keys = _ENGINE_REQUIRED_KEYS.get(engine, [])
    # Vega-Lite wraps its spec in a 'spec' sub-dict
    check_data = data.get('spec', data) if engine == 'vega_lite' else data
    for key in required_keys:
        if key not in check_data:
            errors.append(f"Engine '{engine}' requires data key '{key}' but it is missing")

    if errors:
        return False, errors
    return True, []
