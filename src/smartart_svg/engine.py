"""Constraint-based container engine for SVG layout.

Provides a Container class that can be subdivided into grids, rows, or columns
with proportional sizing. Text fitting with automatic font size reduction.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class FittedText:
    text: str
    font_size: float
    lines: List[str]
    overflow: bool


@dataclass
class Container:
    """A rectangular region that can be subdivided."""
    x: float
    y: float
    width: float
    height: float
    padding: float = 0

    @property
    def inner_x(self):
        return self.x + self.padding

    @property
    def inner_y(self):
        return self.y + self.padding

    @property
    def inner_width(self):
        return max(0, self.width - 2 * self.padding)

    @property
    def inner_height(self):
        return max(0, self.height - 2 * self.padding)

    def center_point(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)

    def split_grid(self, rows: int, cols: int, gap: float = 0) -> List['Container']:
        """Split into a rows x cols grid of equal-sized containers."""
        iw = self.inner_width - gap * (cols - 1)
        ih = self.inner_height - gap * (rows - 1)
        cell_w = iw / cols
        cell_h = ih / rows
        cells = []
        for r in range(rows):
            for c in range(cols):
                cx = self.inner_x + c * (cell_w + gap)
                cy = self.inner_y + r * (cell_h + gap)
                cells.append(Container(cx, cy, cell_w, cell_h))
        return cells

    def split_horizontal(self, ratios: List[float], gap: float = 0) -> List['Container']:
        """Split horizontally by proportional ratios."""
        total = sum(ratios)
        available = self.inner_width - gap * (len(ratios) - 1)
        parts = []
        cx = self.inner_x
        for ratio in ratios:
            w = available * (ratio / total)
            parts.append(Container(cx, self.inner_y, w, self.inner_height))
            cx += w + gap
        return parts

    def split_vertical(self, ratios: List[float], gap: float = 0) -> List['Container']:
        """Split vertically by proportional ratios."""
        total = sum(ratios)
        available = self.inner_height - gap * (len(ratios) - 1)
        parts = []
        cy = self.inner_y
        for ratio in ratios:
            h = available * (ratio / total)
            parts.append(Container(self.inner_x, cy, self.inner_width, h))
            cy += h + gap
        return parts

    def fit_text(self, text: str, font_size: float = 16, max_lines: int = 1) -> FittedText:
        """Reduce font size until text fits within container width.

        Uses approximate character width (0.6 x font_size) for estimation.
        Minimum font size is 10px.
        """
        min_size = 10
        current_size = font_size
        while current_size >= min_size:
            char_width = current_size * 0.6
            chars_per_line = max(1, int(self.inner_width / char_width))
            lines = []
            words = text.split()
            current_line = ""
            for word in words:
                test = (current_line + " " + word).strip()
                if len(test) <= chars_per_line:
                    current_line = test
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            if len(lines) <= max_lines:
                return FittedText(text=text, font_size=current_size, lines=lines, overflow=False)
            current_size -= 1

        # At minimum size, just truncate
        char_width = min_size * 0.6
        chars_per_line = max(1, int(self.inner_width / char_width))
        return FittedText(
            text=text, font_size=min_size,
            lines=[text[:chars_per_line]], overflow=True
        )
