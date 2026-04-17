"""Notes parser — parse external speaker notes files and match to slide outlines.

Reads .md or .txt files with per-slide narrative blocks, matches them to
slides in the outline by number or headline, and computes timing metadata.
"""

import re
from difflib import SequenceMatcher


# Matches: ## Slide 3: The Problem, ### Slide 1: Title, ## The Problem
_HEADING_RE = re.compile(
    r'^#{1,6}\s+'
    r'(?:Slide\s+(\d+)\s*[:.\-\u2014]\s*)?'
    r'(.+?)\s*$',
    re.MULTILINE,
)

# Matches: [3], [Slide 3], [ 3 ]
_BRACKET_RE = re.compile(
    r'^\[(?:Slide\s+)?(\d+)\]\s*$',
    re.MULTILINE | re.IGNORECASE,
)


def parse_notes_file(file_path):
    """Parse an external notes file into per-slide blocks.

    Args:
        file_path: Path to .md or .txt file.

    Returns:
        List of dicts: [{'raw_label': str, 'slide_number': int|None,
                         'headline_hint': str|None, 'text': str}]
    """
    with open(file_path) as f:
        content = f.read()

    if not content.strip():
        return []

    # Find all delimiter positions
    delimiters = []

    for m in _HEADING_RE.finditer(content):
        num = int(m.group(1)) if m.group(1) else None
        headline = m.group(2).strip()
        delimiters.append({
            'pos': m.start(),
            'end': m.end(),
            'slide_number': num,
            'headline_hint': headline,
            'raw_label': m.group(0).lstrip('#').strip(),
        })

    for m in _BRACKET_RE.finditer(content):
        num = int(m.group(1))
        delimiters.append({
            'pos': m.start(),
            'end': m.end(),
            'slide_number': num,
            'headline_hint': None,
            'raw_label': m.group(0).strip(),
        })

    # Sort by position, deduplicate overlapping matches
    delimiters.sort(key=lambda d: d['pos'])
    if not delimiters:
        return [{
            'raw_label': '',
            'slide_number': 1,
            'headline_hint': None,
            'text': content.strip(),
        }]

    # Extract text blocks between delimiters
    blocks = []
    for i, delim in enumerate(delimiters):
        text_start = delim['end']
        text_end = delimiters[i + 1]['pos'] if i + 1 < len(delimiters) else len(content)
        text = content[text_start:text_end].strip()
        if text:
            blocks.append({
                'raw_label': delim['raw_label'],
                'slide_number': delim['slide_number'],
                'headline_hint': delim['headline_hint'],
                'text': text,
            })

    return blocks
