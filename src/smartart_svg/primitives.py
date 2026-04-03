"""SVG building blocks — rect, circle, text, arrow, group, document.

All functions return SVG markup strings. The svg_document wrapper
adds accessibility tags (title, desc) for WCAG 2.2 compliance.
"""


def svg_rect(x, y, w, h, rx=0, fill="#cccccc", stroke=None, class_name=None):
    attrs = f'x="{x}" y="{y}" width="{w}" height="{h}"'
    if rx:
        attrs += f' rx="{rx}"'
    attrs += f' fill="{fill}"'
    if stroke:
        attrs += f' stroke="{stroke}" stroke-width="1"'
    if class_name:
        attrs += f' class="{class_name}"'
    return f'<rect {attrs}/>'


def svg_circle(cx, cy, r, fill="#cccccc", opacity=1.0):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" opacity="{opacity}"/>'


def svg_text(x, y, text, font_family="sans-serif", font_size=16, fill="#000000",
             anchor="start", weight="normal"):
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x}" y="{y}" font-family="{font_family}" font-size="{font_size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{escaped}</text>')


def svg_arrow(x1, y1, x2, y2, stroke="#333333", stroke_width=2):
    mid = "arrow-marker"
    marker = (f'<defs><marker id="{mid}" markerWidth="10" markerHeight="7" '
              f'refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" '
              f'fill="{stroke}"/></marker></defs>')
    line = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
            f'stroke-width="{stroke_width}" marker-end="url(#{mid})"/>')
    return marker + line


def svg_group(children, transform=None, role=None, aria_label=None):
    attrs = ""
    if transform:
        attrs += f' transform="{transform}"'
    if role:
        attrs += f' role="{role}"'
    if aria_label:
        attrs += f' aria-label="{aria_label}"'
    inner = "\n".join(children)
    return f'<g{attrs}>\n{inner}\n</g>'


def svg_document(width, height, children, title="", desc=""):
    inner = "\n".join(children)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">\n'
            f'<title>{title}</title>\n'
            f'<desc>{desc}</desc>\n'
            f'{inner}\n'
            f'</svg>')
