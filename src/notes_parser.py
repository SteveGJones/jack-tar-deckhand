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


def _strip_punctuation(text):
    """Remove punctuation for fuzzy comparison."""
    return re.sub(r'[^\w\s]', '', text).strip()


def _fuzzy_match_headline(hint, headlines):
    """Find the best matching slide for a headline hint.

    Args:
        hint: The headline hint from the parsed block.
        headlines: dict of {slide_number: headline} from the outline.

    Returns:
        slide_number or None.
    """
    hint_clean = _strip_punctuation(hint).lower()
    if not hint_clean:
        return None

    best_match = None
    best_ratio = 0

    for slide_num, headline in headlines.items():
        headline_clean = _strip_punctuation(headline).lower()

        # Substring containment (either direction)
        if hint_clean in headline_clean or headline_clean in hint_clean:
            return slide_num

        # Fuzzy ratio
        ratio = SequenceMatcher(None, hint_clean, headline_clean).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = slide_num

    if best_ratio > 0.7:
        return best_match

    return None


def match_notes_to_outline(parsed_blocks, outline):
    """Match parsed note blocks to slides in the outline.

    Args:
        parsed_blocks: List of dicts from parse_notes_file().
        outline: SlideOutline dict with 'slides' array.

    Returns:
        Tuple of (matched_dict, warnings_list).
        matched_dict: {slide_number: text}
        warnings_list: list of warning strings for unmatched blocks.
    """
    slide_numbers = {s['slide_number'] for s in outline.get('slides', [])}
    headlines = {s['slide_number']: s.get('headline', '') for s in outline.get('slides', [])}

    matched = {}
    warnings = []

    for block in parsed_blocks:
        # Priority 1: explicit slide number
        if block['slide_number'] is not None:
            if block['slide_number'] in slide_numbers:
                matched[block['slide_number']] = block['text']
                continue
            else:
                warnings.append(
                    f"Note for '{block['raw_label']}' references slide {block['slide_number']} "
                    f"which does not exist in the outline — skipped"
                )
                continue

        # Priority 2: headline fuzzy match
        if block['headline_hint']:
            slide_num = _fuzzy_match_headline(block['headline_hint'], headlines)
            if slide_num is not None:
                matched[slide_num] = block['text']
                continue

        # Unmatched
        label = block['raw_label'] or block['headline_hint'] or block['text'][:40]
        warnings.append(f"Note for '{label}' didn't match any slide — skipped")

    return matched, warnings


def estimate_timing(text, wpm=130):
    """Estimate speaking time for a text block.

    Args:
        text: The speaker notes text.
        wpm: Words per minute (default 130 for natural conversational pace).

    Returns:
        int: Estimated seconds, rounded.
    """
    if not text or not text.strip():
        return 0
    word_count = len(text.split())
    seconds = word_count / wpm * 60
    return round(seconds) if seconds > 0 else 0


def _format_timing_marker(total_seconds):
    """Format cumulative seconds as ~M:SS string."""
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f'~{minutes}:{seconds:02d}'


def build_timing_markers(notes_dict, wpm=130):
    """Build timing metadata for each slide's notes.

    Args:
        notes_dict: {slide_number: text} from match_notes_to_outline.
        wpm: Words per minute for timing calculation.

    Returns:
        dict: {slide_number: {'estimated_seconds': int, 'timing_marker': str}}
    """
    if not notes_dict:
        return {}

    markers = {}
    cumulative = 0

    for slide_num in sorted(notes_dict.keys()):
        seconds = estimate_timing(notes_dict[slide_num], wpm=wpm)
        cumulative += seconds
        markers[slide_num] = {
            'estimated_seconds': seconds,
            'timing_marker': _format_timing_marker(cumulative),
        }

    return markers
