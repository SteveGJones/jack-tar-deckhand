"""Static drift detection: every flag in a SKILL.md argument-hint must appear
in the Generate snippet's Python invocation."""
import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILLS = ['openai-image', 'google-image', 'fal-image', 'image']


def _read_skill(name):
    return (PLUGIN_ROOT / 'skills' / name / 'SKILL.md').read_text()


def _argument_hint_flags(text):
    """Return the set of long-form CLI flags declared in argument-hint frontmatter."""
    match = re.search(r'^argument-hint:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
    if not match:
        return set()
    hint = match.group(1)
    return set(re.findall(r'--([a-z][a-z0-9-]*)', hint))


def _generate_block_kwargs(text):
    """Return the set of Python kwargs used in the Generate code block.

    Looks for the first ```bash ... python3 -c ... ``` block that calls
    generate_cloud_image and returns the kwarg names from that call.
    """
    blocks = re.findall(
        r'generate_cloud_image\s*\((.*?)\)',
        text,
        re.DOTALL,
    )
    if not blocks:
        return set()
    body = blocks[0]
    return set(re.findall(r'\b([a-z_][a-z0-9_]*)\s*=', body))


# Map CLI flag name -> kwarg name expected in generate_cloud_image call.
# A flag may legitimately be consumed before generate_cloud_image (eg. --output,
# --provider) so it isn't required to appear as a kwarg.
_NON_KWARG_FLAGS = {'output', 'provider', 'tier', 'colors', 'format'}

# Some flags are CLI-named differently from the kwarg
_FLAG_TO_KWARG = {
    'size': 'size',
    'quality': 'quality',
    'background': 'background',
    'model': 'model',
    'resolution': 'resolution',
}


@pytest.mark.parametrize('skill', SKILLS)
def test_every_documented_flag_reaches_generate_call(skill):
    text = _read_skill(skill)
    flags = _argument_hint_flags(text)
    kwargs = _generate_block_kwargs(text)

    missing = []
    for flag in flags:
        if flag in _NON_KWARG_FLAGS:
            continue
        kwarg = _FLAG_TO_KWARG.get(flag, flag)
        if kwarg not in kwargs:
            missing.append((flag, kwarg))

    assert not missing, (
        f"SKILL.md drift in {skill}: documented flag(s) not threaded "
        f"to generate_cloud_image: {missing}. "
        f"argument-hint flags: {sorted(flags)}; kwargs in Generate: {sorted(kwargs)}"
    )
