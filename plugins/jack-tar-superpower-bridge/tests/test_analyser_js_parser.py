from unittest.mock import patch

import pytest

from src.analyser.js_parser import parse_js, JsParseError, EXEC_GUARD_NAMES


def test_variant_a_recovers_eight_markers(seed_variant_a_build):
    facts = parse_js(seed_variant_a_build)
    total = sum(len(s.markers) for s in facts)
    assert total == 8


def test_variant_b_recovers_markers_that_ooxml_misses(seed_variant_b_build):
    """Variant B used `name:` (dropped by PptxGenJS) — JS parser sees them in source."""
    facts = parse_js(seed_variant_b_build)
    total = sum(len(s.markers) for s in facts)
    assert total >= 1, "Variant B build.js was authored with marker-bearing addShape calls"


def test_parser_never_calls_subprocess_eval_exec_or_require(seed_variant_a_build):
    """Hard contract test: the JS fallback never executes user JavaScript.

    Patches every enumerated guard target with a side_effect that raises if
    invoked. Earlier draft of this test only patched 3 of the 9 targets it
    enumerated — the security panel flagged this. Now we apply ALL patches via
    contextlib.ExitStack so future regressions are caught."""
    import builtins, contextlib, importlib, os, subprocess

    calls: list[str] = []

    def _trip(name):
        def boom(*a, **kw):
            calls.append(name)
            raise AssertionError(f"JS parser must not invoke {name!r}")
        return boom

    targets = [
        (subprocess, "Popen", _trip("subprocess.Popen")),
        (subprocess, "run", _trip("subprocess.run")),
        (subprocess, "call", _trip("subprocess.call")),
        (subprocess, "check_call", _trip("subprocess.check_call")),
        (subprocess, "check_output", _trip("subprocess.check_output")),
        (subprocess, "getoutput", _trip("subprocess.getoutput")),
        (subprocess, "getstatusoutput", _trip("subprocess.getstatusoutput")),
        (builtins, "eval", _trip("builtins.eval")),
        (builtins, "exec", _trip("builtins.exec")),
        (builtins, "compile", _trip("builtins.compile")),
        (os, "system", _trip("os.system")),
        (os, "popen", _trip("os.popen")),
        (importlib, "import_module", _trip("importlib.import_module")),
    ]

    with contextlib.ExitStack() as stack:
        for module, attr, fake in targets:
            if hasattr(module, attr):
                stack.enter_context(patch.object(module, attr, side_effect=fake))
        parse_js(seed_variant_a_build)

    assert calls == [], f"JS parser invoked guarded names: {calls}"


def test_malicious_buildjs_with_top_level_subprocess_does_not_run(tmp_path):
    """A build.js that *would* spawn child_process if executed must not.

    The parser walks the AST; the top-level CallExpression to require()
    is parsed but never invoked.
    """
    malicious = tmp_path / "malicious.js"
    malicious.write_text(
        "require('child_process').execSync('echo OWNED');\n"
        "const pres = new pptxgen();\n"
        "const slide = pres.addSlide();\n"
        "slide.addShape('rect', { objectName: 'IMAGE:safe', x:0, y:0, w:1, h:1 });\n"
    )
    facts = parse_js(malicious)
    # The marker is still recovered because we parse the AST
    total = sum(len(s.markers) for s in facts)
    assert total == 1


def test_unparseable_js_raises_jsparseerror(tmp_path):
    bad = tmp_path / "broken.js"
    bad.write_text("function (((( ")
    with pytest.raises(JsParseError):
        parse_js(bad)


def test_exec_guard_names_documented():
    """The contract is enforced by the test above; this test asserts the guard list."""
    for required in ("subprocess", "eval", "exec", "compile", "os.system",
                      "os.popen", "import_module", "child_process"):
        assert required in EXEC_GUARD_NAMES, f"missing from EXEC_GUARD_NAMES: {required}"
