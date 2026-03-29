"""Tests for prompt translator module."""

import json
import os
import pytest


@pytest.fixture
def style_guide():
    with open('tests/fixtures/valid_style_guide.json') as f:
        return json.load(f)


@pytest.fixture
def visual_direction():
    return "Abstract network of connected nodes in deep blue, conveying interconnected intelligence, clean lines, professional photography style"


class TestTranslatePrompt:
    def test_returns_dict_with_required_fields(self, visual_direction):
        from src.prompt_translator import translate_prompt
        result = translate_prompt(visual_direction, 'x/z-image-turbo')
        assert 'prompt' in result
        assert 'model' in result
        assert 'negative_prompt' in result
        assert 'style_suffix' in result
        assert result['model'] == 'x/z-image-turbo'

    def test_prompt_is_non_empty(self, visual_direction):
        from src.prompt_translator import translate_prompt
        result = translate_prompt(visual_direction, 'x/z-image-turbo')
        assert len(result['prompt']) > 0

    def test_z_image_turbo_is_concise(self, visual_direction):
        from src.prompt_translator import translate_prompt
        result = translate_prompt(visual_direction, 'x/z-image-turbo')
        word_count = len(result['prompt'].split())
        assert word_count <= 75  # budget is ~50 but with style suffix could be up to 75

    def test_flux2_klein_is_detailed(self, visual_direction):
        from src.prompt_translator import translate_prompt
        result = translate_prompt(visual_direction, 'x/flux2-klein')
        # Should preserve more detail than z-image-turbo
        assert 'network' in result['prompt'].lower() or 'connect' in result['prompt'].lower()

    def test_gpt_image_allows_long_prompts(self, visual_direction):
        from src.prompt_translator import translate_prompt
        long_direction = visual_direction + ". " + " ".join(["additional detail"] * 50)
        result = translate_prompt(long_direction, 'gpt-image-1.5')
        # GPT Image supports long prompts — should not truncate aggressively
        word_count = len(result['prompt'].split())
        assert word_count > 20

    def test_with_style_guide(self, visual_direction, style_guide):
        from src.prompt_translator import translate_prompt
        result = translate_prompt(visual_direction, 'x/z-image-turbo', style_guide=style_guide)
        # Style guide should influence the prompt
        prompt_lower = result['prompt'].lower()
        # Should include palette info or style tokens
        assert any(term in prompt_lower for term in ['blue', 'professional', 'clean', '1a365d', 'palette'])

    def test_unknown_model_uses_defaults(self, visual_direction):
        from src.prompt_translator import translate_prompt
        result = translate_prompt(visual_direction, 'unknown-model-xyz')
        assert len(result['prompt']) > 0
        assert result['model'] == 'unknown-model-xyz'


class TestInjectPalette:
    def test_adds_palette_colours(self, style_guide):
        from src.prompt_translator import inject_palette
        prompt = "A sunset over mountains"
        result = inject_palette(prompt, style_guide)
        # Should contain hex colours from the style guide
        assert style_guide['palette']['primary'].lower() in result.lower()

    def test_no_style_guide_returns_original(self):
        from src.prompt_translator import inject_palette
        prompt = "A sunset"
        result = inject_palette(prompt, None)
        assert result == prompt


class TestInjectStyleTokens:
    def test_adds_mood(self, style_guide):
        from src.prompt_translator import inject_style_tokens
        prompt = "A sunset"
        result = inject_style_tokens(prompt, style_guide)
        mood = style_guide['image_style_tokens']['mood']
        assert mood.lower() in result.lower()

    def test_adds_style_modifiers(self, style_guide):
        from src.prompt_translator import inject_style_tokens
        prompt = "A sunset"
        result = inject_style_tokens(prompt, style_guide)
        # At least one modifier should appear
        modifiers = style_guide['image_style_tokens']['style_modifiers']
        assert any(mod.lower() in result.lower() for mod in modifiers)

    def test_no_style_guide_returns_original(self):
        from src.prompt_translator import inject_style_tokens
        result = inject_style_tokens("A sunset", None)
        assert result == "A sunset"

    def test_missing_tokens_section_safe(self):
        from src.prompt_translator import inject_style_tokens
        result = inject_style_tokens("A sunset", {"palette": {}})
        assert result == "A sunset"


class TestGetNegativePrompt:
    def test_ollama_models_have_negative(self):
        from src.prompt_translator import get_negative_prompt
        neg = get_negative_prompt('x/z-image-turbo')
        assert neg is not None
        assert 'text' in neg.lower() or 'watermark' in neg.lower()

    def test_gpt_image_has_no_negative(self):
        from src.prompt_translator import get_negative_prompt
        neg = get_negative_prompt('gpt-image-1.5')
        assert neg is None  # OpenAI doesn't support negative prompts

    def test_unknown_model_returns_none(self):
        from src.prompt_translator import get_negative_prompt
        neg = get_negative_prompt('some-unknown-model')
        assert neg is None


class TestTruncateToBudget:
    def test_short_text_unchanged(self):
        from src.prompt_translator import truncate_to_budget
        text = "A beautiful sunset"
        result = truncate_to_budget(text, 50)
        assert result == text

    def test_long_text_truncated(self):
        from src.prompt_translator import truncate_to_budget
        text = " ".join(["word"] * 100)
        result = truncate_to_budget(text, 10)
        assert len(result.split()) <= 11  # 10 words + possible "..."

    def test_truncated_text_ends_with_ellipsis(self):
        from src.prompt_translator import truncate_to_budget
        text = " ".join(["word"] * 100)
        result = truncate_to_budget(text, 10)
        assert result.endswith('...')

    def test_exact_budget_not_truncated(self):
        from src.prompt_translator import truncate_to_budget
        text = " ".join(["word"] * 10)
        result = truncate_to_budget(text, 10)
        assert result == text
        assert '...' not in result
