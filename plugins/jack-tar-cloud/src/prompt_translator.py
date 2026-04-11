"""Prompt translator — visual_direction → model-specific image prompts.

Translates the visual_direction field from SlideOutline into prompts
optimised for each target model. Different models need different prompt
styles:

- z-image-turbo: ~75 tokens, camera specs, concise
- flux2-klein: ~250 words, spatial hierarchy, detailed
- GPT Image 1.5: unlimited, natural language, descriptive
- FLUX.2 Pro: 30-80 words, photography terms
- Recraft V4: design-centric, hex palette parameter
- Imagen 4: concise, aspect ratio parameter
- Ideogram 3.0: typography specialist

The translator also injects palette colours and image_style_tokens
from the StyleGuide for visual consistency.
"""

# Token/word budget per model
MODEL_BUDGETS = {
    'x/z-image-turbo': {'max_words': 50, 'style': 'concise_camera'},
    'x/flux2-klein': {'max_words': 200, 'style': 'detailed_spatial'},
    'gpt-image-1.5': {'max_words': 500, 'style': 'natural_language'},
    'flux-2-pro': {'max_words': 60, 'style': 'photography'},
    'recraft-v4': {'max_words': 100, 'style': 'design_centric'},
    'imagen-4': {'max_words': 40, 'style': 'concise'},
    'ideogram-3': {'max_words': 80, 'style': 'typography'},
}

# Standard negative prompt for models that support it.
# Text overlay is handled by PptxGenJS — never generate in-image text.
_NEGATIVE_PROMPT = (
    "text, watermark, logo, words, letters, typography, writing, "
    "blurry, low quality, distorted, deformed, ugly, noisy, grainy"
)

# Models that do NOT support negative prompts
_NO_NEGATIVE_PROMPT_MODELS = {'gpt-image-1.5', 'imagen-4'}

# Style-specific prefix additions
_STYLE_PREFIXES = {
    'concise_camera': 'Professional photo, sharp focus, studio lighting. ',
    'detailed_spatial': 'Highly detailed digital artwork. Foreground: ',
    'natural_language': '',
    'photography': 'Photorealistic, DSLR, 85mm lens, f/2.8, natural light. ',
    'design_centric': 'Clean vector-style design, flat illustration. ',
    'concise': 'High quality image. ',
    'typography': 'Clean composition, no text overlays. ',
}

# Always appended to every prompt (text is handled in-slide by PptxGenJS)
_NO_TEXT_SUFFIX = ' No text, no words, no letters.'


def translate_prompt(visual_direction, model, style_guide=None):
    """Translate visual_direction into a model-specific prompt.

    Args:
        visual_direction: Prose description from SlideOutline (e.g.,
            "Abstract network of connected nodes in deep blue")
        model: Target model identifier (e.g., 'x/z-image-turbo')
        style_guide: Optional StyleGuide dict. If provided, injects
            palette colours and image_style_tokens.

    Returns:
        dict: {
            'prompt': str,       # The translated prompt text
            'model': str,        # Target model identifier
            'negative_prompt': str or None,  # Negative prompt (if model supports it)
            'style_suffix': str, # Style modifiers appended
        }
    """
    budget = MODEL_BUDGETS.get(model, {'max_words': 500, 'style': 'natural_language'})
    style = budget['style']
    max_words = budget['max_words']

    # Build the base prompt: prefix + visual direction
    prefix = _STYLE_PREFIXES.get(style, '')
    base = prefix + visual_direction

    # Truncate to budget before injecting style tokens (keeps core intent)
    base = truncate_to_budget(base, max_words)

    # Inject style guide context if provided
    style_suffix = ''
    if style_guide is not None:
        with_palette = inject_palette(base, style_guide)
        with_tokens = inject_style_tokens(with_palette, style_guide)
        # Determine what was added as suffix
        style_suffix = with_tokens[len(base):]
        base = with_tokens

    # Always append the no-text instruction
    prompt = base + _NO_TEXT_SUFFIX

    return {
        'prompt': prompt,
        'model': model,
        'negative_prompt': get_negative_prompt(model),
        'style_suffix': style_suffix,
    }


def inject_palette(prompt, style_guide):
    """Append palette colour information to a prompt.

    Adds the primary, secondary, and accent hex colours to the prompt
    for colour consistency across generated images.

    Returns:
        str: Prompt with palette info appended.
    """
    if not style_guide:
        return prompt

    palette = style_guide.get('palette', {})
    primary = palette.get('primary', '')
    secondary = palette.get('secondary', '')
    accent = palette.get('accent', '')

    if not any([primary, secondary, accent]):
        return prompt

    parts = []
    if primary:
        parts.append(f'primary #{primary}')
    if secondary:
        parts.append(f'secondary #{secondary}')
    if accent:
        parts.append(f'accent #{accent}')

    return prompt + '. Colour palette: ' + ', '.join(parts)


def inject_style_tokens(prompt, style_guide):
    """Append image_style_tokens from the StyleGuide to a prompt.

    Adds mood, color_direction, and style_modifiers for visual consistency.

    Returns:
        str: Prompt with style tokens appended.
    """
    if not style_guide:
        return prompt

    tokens = style_guide.get('image_style_tokens')
    if not tokens:
        return prompt

    mood = tokens.get('mood', '')
    color_direction = tokens.get('color_direction', '')
    modifiers = tokens.get('style_modifiers', [])

    parts = []
    if mood:
        parts.append(mood)
    if color_direction:
        parts.append(color_direction)

    suffix = ''
    if parts:
        suffix += '. Style: ' + ', '.join(parts)
    if modifiers:
        suffix += '. ' + ', '.join(modifiers)

    return prompt + suffix if suffix else prompt


def get_negative_prompt(model):
    """Return the standard negative prompt for a model, or None.

    Negative prompts tell the model what to avoid. Not all models
    support them.
    """
    if model in _NO_NEGATIVE_PROMPT_MODELS:
        return None

    # Only return a negative prompt for known models that support it;
    # unknown models default to None.
    if model in MODEL_BUDGETS:
        return _NEGATIVE_PROMPT

    return None


def truncate_to_budget(text, max_words):
    """Truncate text to fit within a word budget.

    Truncates at word boundaries. Adds '...' if truncated.

    Returns:
        str: Text within the word budget.
    """
    words = text.split()
    if len(words) <= max_words:
        return text
    return ' '.join(words[:max_words]) + '...'
