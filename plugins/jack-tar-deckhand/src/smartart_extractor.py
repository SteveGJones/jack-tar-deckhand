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


def _format_flowchart_label(point):
    """Format a long flowchart label with line breaks for taller, more readable nodes.

    Pattern: 'Header: item1, item2, item3' becomes 'Header:<br/>item1<br/>item2<br/>item3'
    Long labels without that structure are split heuristically on the most natural break.
    Uses <br/> which Mermaid renders as a line break inside foreignObject node labels.
    """
    cleaned = _clean_label(point)
    if ':' in cleaned and ',' in cleaned:
        header, rest = cleaned.split(':', 1)
        items = [it.strip() for it in rest.split(',') if it.strip()]
        return f"{header.strip()}:<br/>" + "<br/>".join(items)
    if ':' in cleaned:
        header, rest = cleaned.split(':', 1)
        return f"{header.strip()}:<br/>{rest.strip()}"
    return cleaned


def _body_points_to_tree(body_points):
    """Convert indent-prefixed body_points into a nested tree for org_chart.

    The speaker writes something like:

        CEO
          CTO
            Backend Lead
            Frontend Lead
          CFO
            Finance Manager

    (2-space indentation = one level deeper). This function parses
    that into a tree dict. The first line becomes the root.

    Assistant detection: a line ending with ' (asst)' or '[asst]' is
    marked as an assistant node.

    Returns None if body_points is empty or the first line has leading
    indentation (no root identifiable).
    """
    if not body_points:
        return None

    def _parse_line(line):
        """Return (indent_level, title, is_asst)."""
        stripped_left = line.rstrip()
        indent = len(stripped_left) - len(stripped_left.lstrip(' '))
        level = indent // 2
        title = stripped_left.strip()
        is_asst = False
        for marker in (' (asst)', ' [asst]'):
            if title.lower().endswith(marker):
                is_asst = True
                title = title[: -len(marker)].strip()
                break
        return level, _clean_label(title), is_asst

    first_level, root_title, root_asst = _parse_line(body_points[0])
    if first_level != 0:
        return None  # can't identify a root

    root = {"title": root_title}
    if root_asst:
        root["asst"] = True
    # Stack of (level, node) pairs for current path in the tree
    stack = [(0, root)]

    for line in body_points[1:]:
        if not line.strip():
            continue
        level, title, is_asst = _parse_line(line)
        if level <= 0:
            # Back to root level — attach as sibling of root (but we
            # only have one root in orgChart), so treat as direct child
            # of the root to avoid data loss.
            level = 1

        # Pop the stack until we find the parent at (level - 1)
        while stack and stack[-1][0] >= level:
            stack.pop()
        if not stack:
            # Orphaned — attach to root
            parent = root
        else:
            parent = stack[-1][1]

        node = {"title": title}
        if is_asst:
            node["asst"] = True
        parent.setdefault("children", []).append(node)
        stack.append((level, node))

    return root


_PPTX_NATIVE_HIERARCHICAL_TYPES = {"org_chart", "hierarchy"}
_PPTX_NATIVE_FLAT_TYPES = {
    "flowchart",
    "cycle",
    "list",
    "chevron_list",
    "matrix",
    "pyramid",
    "venn",
    "pipeline_funnel",
    "target",
}


def _extract_pptx_native(body_points, graphic_type):
    """Build the data shape the pptx_native engine's generic builders expect.

    All flat-list layouts (process, cycle, list, chevron, matrix,
    pyramid, venn, funnel, target) use the canonical `{"items": [...]}`
    shape — the flat_list builder accepts it directly. Legacy keys
    (`steps`, `stages`) from Phase 1-7 are still accepted by the
    builder for backward compatibility.

    All hierarchical layouts (org_chart, hierarchy) use the canonical
    `{"tree": {...}}` shape. body_points is parsed as
    indentation-delimited tree (2-space indent per level). A line
    ending with ' (asst)' or ' [asst]' becomes an assistant node —
    only meaningful for orgChart1 which supports the asst node type.

    Args:
        body_points: Raw body_points strings from the slide outline.
        graphic_type: The graphic_type from the selection.

    Returns:
        Dict with 'engine' set to 'pptx_native', 'graphic_type', and
        a 'data' key containing the shape-appropriate structure.
    """
    cleaned_labels = [_clean_label(p) for p in body_points if _clean_label(p)]

    if graphic_type in _PPTX_NATIVE_FLAT_TYPES:
        return {
            'engine': 'pptx_native',
            'graphic_type': graphic_type,
            'data': {'items': cleaned_labels},
        }

    if graphic_type in _PPTX_NATIVE_HIERARCHICAL_TYPES:
        tree = _body_points_to_tree(body_points)
        if tree is None:
            # Fallback if we couldn't parse the indentation — use
            # first as root, rest as direct children
            if cleaned_labels:
                tree = {
                    "title": cleaned_labels[0],
                    "children": [{"title": l} for l in cleaned_labels[1:]],
                }
            else:
                tree = {"title": "", "children": []}
        return {
            'engine': 'pptx_native',
            'graphic_type': graphic_type,
            'data': {'tree': tree},
        }

    # Unsupported graphic_type — fall through with a generic items list.
    # The engine will fail to find a matching layout and return
    # status='failed' via the catalog lookup.
    return {
        'engine': 'pptx_native',
        'graphic_type': graphic_type,
        'data': {'items': cleaned_labels},
    }


def _extract_flowchart(body_points):
    """Build a Mermaid flowchart syntax string with LR layout.

    Routing for 4+ node flowcharts to a custom_svg grid layout happens in
    the higher-level extract() function so the engine can be switched.
    """
    lines = ['graph LR']
    node_ids = []
    for i, point in enumerate(body_points):
        nid = _node_id(i)
        node_ids.append(nid)
        label = _format_flowchart_label(point)
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
    """Parse decision tree from body_points into a branching Mermaid graph.

    Each body_point is parsed as 'question? Yes: outcome' (or similar). The
    output is a top-down (graph TB) tree where each question is a diamond
    node, each outcome is a rectangle leaf, the Yes branch leads to the
    outcome, and the No branch cascades to the next question.
    """
    lines = ['graph TB']

    if not body_points:
        return {
            'engine': 'mermaid',
            'syntax': '\n'.join(lines),
            'diagram_type': 'decision_tree',
            'node_count': 0,
        }

    for i, point in enumerate(body_points):
        q_id = f'Q{i + 1}'
        o_id = f'O{i + 1}'

        # Parse "Is X? Yes: outcome" format
        if '?' in point:
            question, after = point.split('?', 1)
            question = _clean_label(question.strip()) + '?'
            outcome = after
            for prefix in ['Yes:', 'Yes ', 'yes:', 'yes ']:
                if prefix in after:
                    outcome = after.split(prefix, 1)[1].strip()
                    break
            outcome = _clean_label(outcome).rstrip('.')
            if not outcome:
                outcome = 'Decision'
        else:
            question = _clean_label(point)
            outcome = 'Decision'

        # Diamond question node
        lines.append(f'  {q_id}{{"{question}"}}')
        # Rectangle outcome leaf
        lines.append(f'  {o_id}["{outcome}"]')
        # Yes branch leads to the outcome
        lines.append(f'  {q_id} -->|Yes| {o_id}')
        # No branch cascades to the next question (if any)
        if i < len(body_points) - 1:
            next_q_id = f'Q{i + 2}'
            lines.append(f'  {q_id} -->|No| {next_q_id}')

    syntax = '\n'.join(lines)
    return {
        'engine': 'mermaid',
        'syntax': syntax,
        'diagram_type': 'decision_tree',
        'node_count': len(body_points) * 2,
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
        'flowchart': _extract_flowchart_spatial,
        'decision_tree': _extract_decision_tree_spatial,
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

_MERMAID_GRAPHIC_TYPES = {'flowchart', 'decision_tree'}
_VEGA_GRAPHIC_TYPES = {'bar_chart', 'line_chart', 'radar_chart'}
_SPATIAL_GRAPHIC_TYPES = {'swot', 'timeline', 'pipeline_funnel', 'feature_matrix', 'venn', 'gantt', 'flowchart', 'decision_tree'}


def _extract_flowchart_spatial(body_points):
    """Parse body_points into a flowchart node list for the custom_svg layout."""
    return {'nodes': [_clean_label(p) for p in body_points]}


def _extract_decision_tree_spatial(body_points):
    """Parse body_points into question→outcome rules for the custom_svg layout.

    Each body_point is parsed as 'question? Yes: outcome'. Same parsing logic as
    the Mermaid version but flattened into a list of {question, outcome} dicts.
    """
    rules = []
    for point in body_points:
        if '?' in point:
            question, after = point.split('?', 1)
            question = _clean_label(question.strip()) + '?'
            outcome = after
            for prefix in ['Yes:', 'Yes ', 'yes:', 'yes ']:
                if prefix in after:
                    outcome = after.split(prefix, 1)[1].strip()
                    break
            outcome = _clean_label(outcome).rstrip('.')
            if not outcome:
                outcome = 'Decision'
        else:
            question = _clean_label(point)
            outcome = 'Decision'
        rules.append({'question': question, 'outcome': outcome})
    return {'rules': rules}


def _build_vega_from_inline(inline_data, graphic_type, engine='vega_lite'):
    """Build a Vega-Lite spec from structured inline_data."""
    series = inline_data.get('series', [])
    values = [{'label': item['label'], 'value': item['value']} for item in series]

    mark = 'bar'
    if graphic_type == 'line_chart':
        mark = 'line'
    elif graphic_type == 'radar_chart':
        mark = 'point'

    # Optional editorial fields from inline_data
    x_title = inline_data.get('x_axis_title')  # None or "" hides
    y_title = inline_data.get('y_axis_title')
    y_format = inline_data.get('y_format')      # e.g., 'd' for integer, '$,' for currency
    highlight_label = inline_data.get('highlight_label')

    # Detect integer-only data -> force integer ticks
    all_int = all(isinstance(v['value'], int) for v in values) if values else False

    x_encoding = {'field': 'label', 'type': 'ordinal', 'sort': None}
    y_encoding = {'field': 'value', 'type': 'quantitative'}

    # Apply axis titles (None = hidden)
    x_encoding['axis'] = {'title': x_title if x_title else None}
    y_axis = {'title': y_title if y_title else None}

    # Integer formatting
    if all_int and not y_format:
        y_axis['format'] = 'd'
        y_axis['tickMinStep'] = 1
    elif y_format:
        y_axis['format'] = y_format
    y_encoding['axis'] = y_axis

    spec = {
        '$schema': 'https://vega.github.io/schema/vega-lite/v5.json',
        'mark': mark,
        'data': {'values': values},
        'encoding': {
            'x': x_encoding,
            'y': y_encoding
        }
    }

    # Highlight encoding for total/sum bars
    if highlight_label:
        # Use Vega-Lite conditional encoding to colour the highlighted bar differently
        spec['encoding']['color'] = {
            'condition': {
                'test': f"datum.label === '{highlight_label}'",
                'value': '#C67B2F'  # accent colour
            },
            'value': '#1B3A4B'  # primary colour
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

    # Re-route flowcharts with 4+ nodes to custom_svg — Mermaid LR produces a
    # ~5:1 horizontal strip that doesn't fit the slide's 16:9 zone well, while
    # the custom_svg flowchart layout uses an optimal 2x2/2x3/3x3 grid.
    if graphic_type == 'flowchart' and engine == 'mermaid' and len(body_points) >= 4:
        engine = 'custom_svg'

    # Re-route decision trees with 3+ rules to custom_svg — Mermaid TB cascades
    # produce a tall narrow strip that becomes unreadable when fit into a 16:9
    # slide zone. The custom_svg decision_tree layout uses a 2-column "if/then"
    # row layout that fills the slide width comfortably.
    if graphic_type == 'decision_tree' and engine == 'mermaid' and len(body_points) >= 3:
        engine = 'custom_svg'

    # pptx_native takes highest priority once selected — the engine has
    # its own per-layout data shape that differs from the rasterising
    # engines. Phase 2.2 wiring; Phase 4 adds cycle/orgChart/timeline
    # mappings as more layouts come online.
    if engine == 'pptx_native':
        if inline_data is not None:
            # Passthrough — assume inline data is already shaped for the
            # target layout (e.g. {"steps": [...]} for process1). The
            # renderer's layout builder will validate shape.
            data_payload = inline_data
        else:
            extracted_data = _extract_pptx_native(body_points, graphic_type)
            data_payload = extracted_data['data']

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
            'overflow_applied': 'none',
            'style_tokens': style_tokens,
            'validation_status': 'valid' if valid else 'invalid',
            'comparator_engines': [],
        }

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
            extracted_data = {'engine': 'custom_svg', 'graphic_type': graphic_type, 'data': inline_data}
        elif graphic_type in _VEGA_GRAPHIC_TYPES:
            extracted_data = _build_vega_from_inline(inline_data, graphic_type, engine)
        else:
            # For other engines, inline_data is passed through as-is
            extracted_data = {'engine': engine, 'graphic_type': graphic_type, 'data': inline_data}
    elif engine == 'custom_svg':
        # Custom SVG takes priority once selected (the override above re-routes
        # 4+ node flowcharts here even though graphic_type is in MERMAID set).
        extracted_data = extract_spatial_data(body_points, graphic_type)
    elif engine == 'mermaid' or graphic_type in _MERMAID_GRAPHIC_TYPES:
        extracted_data = extract_graph_data(body_points, graphic_type)
    elif engine == 'vega_lite' or engine == 'matplotlib' or graphic_type in _VEGA_GRAPHIC_TYPES:
        extracted_data = extract_series_data(body_points, graphic_type, engine=engine)
    elif graphic_type in _SPATIAL_GRAPHIC_TYPES:
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
    'pptx_native': [],  # per-layout shape validated by the layout builder itself
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
