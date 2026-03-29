#!/usr/bin/env python3
"""
Pipeline Flow Renderer — generates a styled SVG sequence diagram
for the Jack-Tar Deckhand presentation engineering pipeline.

Uses Graphviz for layout computation (dot -Tjson), then generates
custom styled SVG consistent with the service architecture renderer.

Usage:
    python3 pipeline_flow_renderer.py <output.svg>
"""

import json
import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# Style (consistent with service architecture renderer)
# ---------------------------------------------------------------------------

COLORS = {
    "bg": "#FAFBFC",
    "border": "#E5E7EB",
    "ai_persona": "#4338CA",      # Indigo for AI personas
    "ai_persona_light": "#EEF2FF",
    "service": "#0369A1",          # Blue for services
    "service_light": "#F0F9FF",
    "actor": "#047857",            # Green for human actors
    "actor_light": "#ECFDF5",
    "decision": "#B45309",         # Amber for decisions
    "decision_light": "#FFFBEB",
    "flow": "#64748B",
    "flow_highlight": "#4338CA",
    "text_dark": "#1A202C",
    "text_mid": "#475569",
    "text_light": "#64748B",
    "loop_bg": "#FEF3C7",
    "loop_border": "#F59E0B",
}

FONT = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"

# ---------------------------------------------------------------------------
# Pipeline Steps
# ---------------------------------------------------------------------------

STEPS = [
    # Setup
    {"id": "s1",  "label": "1. TalkBrief",           "sublabel": "Speaker submits brief",           "type": "actor",    "lane": "Speaker",    "phase": "setup"},
    {"id": "s2",  "label": "2. Provider Discovery",   "sublabel": "Probe available image providers", "type": "service",  "lane": "Conductor",  "phase": "setup"},
    {"id": "s3",  "label": "3. Budget Confirmation",  "sublabel": "Present options, get approval",   "type": "actor",    "lane": "Speaker",    "phase": "setup"},
    # Draft cycle (iterative, cheap)
    {"id": "s4",  "label": "4. Derive StyleGuide",    "sublabel": "Palette, fonts, layout rules",    "type": "service",  "lane": "Design",     "phase": "draft"},
    {"id": "s5",  "label": "5. Generate Outline",     "sublabel": "Slide structure + speaker notes",  "type": "service",  "lane": "Content",    "phase": "draft"},
    {"id": "s6",  "label": "6. Draft Images",         "sublabel": "Ollama or cloud at reduced quality", "type": "service",  "lane": "Image",    "phase": "draft"},
    {"id": "s7",  "label": "7. Build Draft PPTX",     "sublabel": "Assemble with draft images",      "type": "service",  "lane": "Assembly",   "phase": "draft"},
    {"id": "s8",  "label": "8. Speaker Review",       "sublabel": "Iterate or approve for production", "type": "decision", "lane": "Speaker",  "phase": "draft"},
    # Production (single pass, full quality)
    {"id": "s9",  "label": "9. Production Images",    "sublabel": "Full quality, best providers",    "type": "service",  "lane": "Image",      "phase": "production"},
    {"id": "s10", "label": "10. Build Final PPTX",    "sublabel": "Assemble + QA (25 checks)",      "type": "service",  "lane": "Assembly",   "phase": "production"},
    {"id": "s11", "label": "11. Presentation Review",  "sublabel": "Conference best practices",      "type": "ai_persona", "lane": "Reviewer", "phase": "production"},
    {"id": "s12", "label": "12. Deliver",              "sublabel": ".pptx + Review + Cost report",   "type": "actor",    "lane": "Speaker",    "phase": "production"},
]

EDGES = [
    ("s1", "s2"), ("s2", "s3"), ("s3", "s4"), ("s4", "s5"),
    ("s5", "s6"), ("s6", "s7"), ("s7", "s8"),
    ("s8", "s4", "iterate"),
    ("s8", "s9", "approve"),
    ("s9", "s10"), ("s10", "s11"), ("s11", "s12"),
]

LANES = ["Speaker", "Conductor", "Design", "Content", "Image", "Assembly", "Reviewer"]
LANE_TYPES = {
    "Speaker": "actor",
    "Conductor": "ai_persona",
    "Design": "service",
    "Content": "service",
    "Image": "service",
    "Assembly": "service",
    "Reviewer": "ai_persona",
}

# ---------------------------------------------------------------------------
# SVG Generation
# ---------------------------------------------------------------------------

def escape_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


PHASE_COLORS = {
    "setup":      {"bg": "#F8FAFC", "border": "#CBD5E1", "label": "SETUP"},
    "draft":      {"bg": "#FFFBEB", "border": "#F59E0B", "label": "DRAFT CYCLE (iterative, reduced quality)"},
    "production": {"bg": "#EFF6FF", "border": "#3B82F6", "label": "PRODUCTION (single pass, full quality)"},
}


def generate_pipeline_svg():
    # Layout constants
    margin_left = 40
    margin_top = 80
    step_width = 220
    step_height = 60
    h_gap = 40
    v_lane_height = 80
    cols_per_row = 4
    row_height = step_height + v_lane_height

    positions = {}
    for i, step in enumerate(STEPS):
        col = i % cols_per_row
        row = i // cols_per_row
        x = margin_left + col * (step_width + h_gap)
        y = margin_top + row * row_height
        positions[step["id"]] = (x, y)

    # Canvas size
    max_col = min(len(STEPS), cols_per_row)
    num_rows = (len(STEPS) + cols_per_row - 1) // cols_per_row
    canvas_w = margin_left + max_col * (step_width + h_gap) + 40
    canvas_h = margin_top + num_rows * row_height + 60

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" '
               f'width="{canvas_w}" height="{canvas_h}" font-family="{escape_xml(FONT)}">')

    # Definitions
    svg.append('<defs>')
    svg.append('  <filter id="shadow" x="-4%" y="-4%" width="108%" height="116%">')
    svg.append('    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.08"/>')
    svg.append('  </filter>')
    svg.append('  <marker id="arrow" viewBox="0 0 10 7" refX="10" refY="3.5" '
               'markerWidth="8" markerHeight="6" orient="auto-start-reverse">')
    svg.append(f'    <polygon points="0 0, 10 3.5, 0 7" fill="{COLORS["flow"]}"/>')
    svg.append('  </marker>')
    svg.append('  <marker id="arrow-iterate" viewBox="0 0 10 7" refX="10" refY="3.5" '
               'markerWidth="8" markerHeight="6" orient="auto-start-reverse">')
    svg.append(f'    <polygon points="0 0, 10 3.5, 0 7" fill="{COLORS["loop_border"]}"/>')
    svg.append('  </marker>')
    svg.append('  <marker id="arrow-approve" viewBox="0 0 10 7" refX="10" refY="3.5" '
               'markerWidth="8" markerHeight="6" orient="auto-start-reverse">')
    svg.append(f'    <polygon points="0 0, 10 3.5, 0 7" fill="#3B82F6"/>')
    svg.append('  </marker>')
    svg.append('</defs>')

    # Background
    svg.append(f'<rect width="{canvas_w}" height="{canvas_h}" fill="{COLORS["bg"]}"/>')

    # Title
    svg.append(f'<text x="{canvas_w // 2}" y="35" text-anchor="middle" '
               f'font-size="20" font-weight="700" fill="{COLORS["text_dark"]}" '
               f'letter-spacing="-0.4">Pipeline Execution Flow</text>')
    svg.append(f'<text x="{canvas_w // 2}" y="55" text-anchor="middle" '
               f'font-size="12" font-weight="500" fill="{COLORS["text_light"]}" '
               f'letter-spacing="0.2">JACK-TAR DECKHAND — DRAFT / PRODUCTION LIFECYCLE</text>')

    # Draw phase background zones
    phase_rows = {}
    for i, step in enumerate(STEPS):
        phase = step["phase"]
        row = i // cols_per_row
        col = i % cols_per_row
        if phase not in phase_rows:
            phase_rows[phase] = {"min_row": row, "max_row": row, "min_col": col, "max_col": col}
        else:
            phase_rows[phase]["min_row"] = min(phase_rows[phase]["min_row"], row)
            phase_rows[phase]["max_row"] = max(phase_rows[phase]["max_row"], row)
            phase_rows[phase]["min_col"] = min(phase_rows[phase]["min_col"], col)
            phase_rows[phase]["max_col"] = max(phase_rows[phase]["max_col"], col)

    for phase, info in phase_rows.items():
        pc = PHASE_COLORS[phase]
        py = margin_top + info["min_row"] * row_height - 20
        ph = (info["max_row"] - info["min_row"] + 1) * row_height + 10
        px = margin_left - 15
        pw = canvas_w - margin_left * 2 + 30
        svg.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" '
                   f'rx="12" fill="{pc["bg"]}" stroke="{pc["border"]}" stroke-width="1" '
                   f'stroke-dasharray="4,3" opacity="0.7"/>')
        svg.append(f'<text x="{px + 12}" y="{py + 14}" font-size="10" font-weight="600" '
                   f'fill="{pc["border"]}" letter-spacing="0.3">{pc["label"]}</text>')

    # Draw edges (behind nodes)
    for edge in EDGES:
        src_id, tgt_id = edge[0], edge[1]
        label = edge[2] if len(edge) > 2 else None

        sx, sy = positions[src_id]
        tx, ty = positions[tgt_id]
        scx, scy = sx + step_width / 2, sy + step_height / 2
        tcx, tcy = tx + step_width / 2, ty + step_height / 2

        is_iterate = label == "iterate"
        is_approve = label == "approve"

        if is_iterate:
            stroke = COLORS["loop_border"]
            marker = "arrow-iterate"
            dash = ' stroke-dasharray="6,4"'
            width = "2"
        elif is_approve:
            stroke = "#3B82F6"
            marker = "arrow-approve"
            dash = ""
            width = "2.5"
        else:
            stroke = COLORS["flow"]
            marker = "arrow"
            dash = ""
            width = "1.5"

        if is_iterate:
            # Loop back: curved path going up
            x1, y1 = sx + step_width / 2, sy
            x2, y2 = tx + step_width / 2, ty + step_height
            mid_y = min(sy, ty) - 30
            svg.append(f'<path d="M {x1} {y1} '
                       f'C {x1} {mid_y}, {x2} {mid_y}, {x2} {y2}" '
                       f'stroke="{stroke}" stroke-width="{width}" fill="none" '
                       f'marker-end="url(#{marker})"{dash}/>')
            mid_x = (x1 + x2) / 2
            svg.append(f'<rect x="{mid_x - 30}" y="{mid_y - 10}" width="60" height="18" rx="3" '
                       f'fill="{COLORS["loop_bg"]}" stroke="{COLORS["loop_border"]}" stroke-width="1"/>')
            svg.append(f'<text x="{mid_x}" y="{mid_y + 3}" text-anchor="middle" '
                       f'font-size="9" font-weight="600" fill="{COLORS["decision"]}">ITERATE</text>')
        elif sy == ty:
            # Same row
            x1, y1 = sx + step_width, scy
            x2, y2 = tx, tcy
            svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                       f'stroke="{stroke}" stroke-width="{width}" marker-end="url(#{marker})"{dash}/>')
            if is_approve:
                lx = (x1 + x2) / 2
                svg.append(f'<rect x="{lx - 32}" y="{y1 - 18}" width="64" height="16" rx="3" '
                           f'fill="#EFF6FF" stroke="#3B82F6" stroke-width="1"/>')
                svg.append(f'<text x="{lx}" y="{y1 - 7}" text-anchor="middle" '
                           f'font-size="9" font-weight="600" fill="#3B82F6">APPROVE</text>')
        else:
            # Different row
            src_col = [i for i, s in enumerate(STEPS) if s["id"] == src_id][0] % cols_per_row
            tgt_col = [i for i, s in enumerate(STEPS) if s["id"] == tgt_id][0] % cols_per_row

            if src_col >= tgt_col:
                # Wrap to next row
                x1, y1 = scx, sy + step_height
                x2, y2 = tcx, ty
                mid_y = (y1 + y2) / 2
                svg.append(f'<path d="M {x1} {y1} C {x1} {mid_y}, {x2} {mid_y}, {x2} {y2}" '
                           f'stroke="{stroke}" stroke-width="{width}" fill="none" '
                           f'marker-end="url(#{marker})"{dash}/>')
            else:
                x1, y1 = sx + step_width, scy
                x2, y2 = tx, tcy
                svg.append(f'<path d="M {x1} {y1} C {x1 + 20} {y1}, {x2 - 20} {y2}, {x2} {y2}" '
                           f'stroke="{stroke}" stroke-width="{width}" fill="none" '
                           f'marker-end="url(#{marker})"{dash}/>')

    # Draw step nodes
    for step in STEPS:
        x, y = positions[step["id"]]
        t = step["type"]
        header_color = COLORS[t]
        lane = step["lane"]

        svg.append(f'<g filter="url(#shadow)">')
        svg.append(f'  <rect x="{x}" y="{y}" width="{step_width}" height="{step_height}" '
                   f'rx="8" fill="white" stroke="{COLORS["border"]}" stroke-width="1"/>')
        svg.append(f'</g>')

        svg.append(f'<rect x="{x}" y="{y}" width="{step_width}" height="24" '
                   f'rx="8" fill="{header_color}"/>')
        svg.append(f'<rect x="{x}" y="{y + 16}" width="{step_width}" height="8" '
                   f'fill="{header_color}"/>')

        badge_text = f"[AI] {lane}" if LANE_TYPES.get(lane) == "ai_persona" else lane
        svg.append(f'<text x="{x + 8}" y="{y + 16}" font-size="11" font-weight="600" '
                   f'fill="white">{escape_xml(step["label"])}</text>')

        svg.append(f'<text x="{x + 8}" y="{y + 40}" font-size="10" font-weight="400" '
                   f'fill="{COLORS["text_mid"]}">{escape_xml(step["sublabel"])}</text>')

        svg.append(f'<text x="{x + step_width - 8}" y="{y + 55}" text-anchor="end" '
                   f'font-size="9" font-weight="500" fill="{COLORS["text_light"]}" '
                   f'letter-spacing="0.2">{escape_xml(badge_text)}</text>')

    # Legend
    legend_y = canvas_h - 40
    legend_items = [
        ("Human Actor", COLORS["actor"]),
        ("AI Persona", COLORS["ai_persona"]),
        ("Service", COLORS["service"]),
        ("Decision", COLORS["decision"]),
    ]
    lx = margin_left
    for label, color in legend_items:
        svg.append(f'<rect x="{lx}" y="{legend_y}" width="12" height="12" rx="2" fill="{color}"/>')
        svg.append(f'<text x="{lx + 18}" y="{legend_y + 10}" font-size="10" font-weight="500" '
                   f'fill="{COLORS["text_mid"]}">{label}</text>')
        lx += 120

    svg.append('</svg>')
    return '\n'.join(svg)


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else 'pipeline-flow.svg'
    svg = generate_pipeline_svg()
    with open(output_path, 'w') as f:
        f.write(svg)
    print(f"Generated: {output_path}")
    print(f"  Steps: {len(STEPS)}")
    print(f"  Edges: {len(EDGES)}")


if __name__ == '__main__':
    main()
