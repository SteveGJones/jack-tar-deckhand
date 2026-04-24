"""esprima AST-based JS parser — marker-extraction fallback only.

Hard contract: this module NEVER executes, imports, requires, or spawns
the input JavaScript. It only walks the AST and extracts literal values
out of `slide.addShape(..., { objectName|name: "...", x, y, w, h })`
calls. EXEC_GUARD_NAMES enumerates the things callers can grep for.

Lifted from Spike 3's parsers/js_parser.py with a new top-level
JsParseError class (the spike crashed with the raw esprima exception).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import esprima

from src.placeholder import parse_marker
from src.slide_facts import Marker, SlideFacts

EXEC_GUARD_NAMES = (
    # Python-side names the parser must never call
    "subprocess", "eval", "exec", "compile", "import_module", "os.system", "os.popen",
    # JavaScript-side names whose presence in build.js is a "would have spawned"
    # signal (parsing them is fine; executing them is what we forbid)
    "child_process", "spawn", "execSync", "execFile", "fork",
)

EMU_PER_INCH = 914400

EvalEnv = dict[str, Any]
SlideBindings = dict[str, SlideFacts]


class JsParseError(RuntimeError):
    """Raised when the JS source cannot be parsed."""


def _resolve_node(node, eval_env: EvalEnv) -> Any:
    if node is None:
        return None
    t = node.type

    if t == "Literal":
        return node.value

    if t == "Identifier":
        return eval_env.get(node.name)

    if t == "UnaryExpression" and node.operator == "-":
        v = _resolve_node(node.argument, eval_env)
        return -v if v is not None else None

    if t == "TemplateLiteral":
        parts = []
        quasis = node.quasis
        exprs = node.expressions
        for i, quasi in enumerate(quasis):
            cooked = quasi.value.cooked or ""
            parts.append(cooked)
            if i < len(exprs):
                val = _resolve_node(exprs[i], eval_env)
                if val is None:
                    return None
                parts.append(str(val))
        return "".join(parts)

    if t == "BinaryExpression" and node.operator == "+":
        l = _resolve_node(node.left, eval_env)
        r = _resolve_node(node.right, eval_env)
        if l is not None and r is not None:
            try:
                return l + r
            except TypeError:
                return None

    return None


def _extract_object_properties_with_env(obj_node, eval_env: EvalEnv) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if obj_node is None or obj_node.type != "ObjectExpression":
        return out
    for prop in obj_node.properties:
        if prop.type != "Property":
            continue
        key = prop.key.name if prop.key.type == "Identifier" else prop.key.value
        val = _resolve_node(prop.value, eval_env)
        out[key] = val
    return out


def _inches_to_emu(v: Any) -> int:
    if v is None:
        return 0
    try:
        return int(float(v) * EMU_PER_INCH)
    except (TypeError, ValueError):
        return 0


def parse_js(path: Path | str) -> list[SlideFacts]:
    """Parse a build.js → list[SlideFacts]. Markers are recovered from
    `slide.addShape(..., { objectName|name: 'KIND:identifier', ... })` calls.

    Raises JsParseError on unparseable input.
    """
    source = Path(path).read_text()
    try:
        tree = esprima.parseScript(source, options={"tolerant": True})
    except esprima.Error as exc:
        raise JsParseError(f"failed to parse {path}: {exc}") from exc
    except Exception as exc:  # esprima sometimes raises non-Error subclasses
        raise JsParseError(f"failed to parse {path}: {exc}") from exc

    helpers: dict[str, tuple[list, list]] = {}
    for stmt in tree.body:
        if stmt.type == "FunctionDeclaration" and stmt.params:
            helpers[stmt.id.name] = (stmt.params, stmt.body.body)

    slides_list: list[SlideFacts] = []

    def _new_slide() -> SlideFacts:
        sf = SlideFacts(slide_index=len(slides_list) + 1, text_content="")
        slides_list.append(sf)
        return sf

    def _is_add_slide_call(call) -> bool:
        callee = call.callee
        return (callee.type == "MemberExpression"
                and callee.property.type == "Identifier"
                and callee.property.name == "addSlide")

    def _handle_add_text(facts: SlideFacts, call, eval_env: EvalEnv):
        if not call.arguments:
            return
        arg0 = call.arguments[0]
        val = _resolve_node(arg0, eval_env)
        if isinstance(val, str):
            facts.text_content = (facts.text_content + "\n" + val).strip()
            return
        if arg0.type == "ArrayExpression":
            parts: list[str] = []
            for el in arg0.elements:
                if el is None:
                    continue
                v = _resolve_node(el, eval_env)
                if isinstance(v, str):
                    parts.append(v)
                elif el.type == "ObjectExpression":
                    props = _extract_object_properties_with_env(el, eval_env)
                    if isinstance(props.get("text"), str):
                        parts.append(props["text"])
            if parts:
                facts.text_content = (facts.text_content + "\n" + "\n".join(parts)).strip()

    def _handle_add_shape(facts: SlideFacts, call, eval_env: EvalEnv):
        if len(call.arguments) < 2:
            return
        props = _extract_object_properties_with_env(call.arguments[1], eval_env)
        object_name = props.get("objectName") or props.get("name")
        if isinstance(object_name, str):
            parsed = parse_marker(object_name.lower() if object_name and ":" in object_name and not object_name.startswith(("IMAGE", "SMARTART", "BG")) else object_name)
            if parsed is not None:
                kind, ident = parsed
                facts.markers.append(Marker(
                    kind=kind,
                    identifier=ident,
                    left_emu=_inches_to_emu(props.get("x")),
                    top_emu=_inches_to_emu(props.get("y")),
                    width_emu=_inches_to_emu(props.get("w")),
                    height_emu=_inches_to_emu(props.get("h")),
                ))
                return
        facts.element_types["shape"] = facts.element_types.get("shape", 0) + 1

    def _apply_method(facts: SlideFacts, method: str, call, eval_env: EvalEnv):
        if method == "addText":
            _handle_add_text(facts, call, eval_env)
        elif method == "addShape":
            _handle_add_shape(facts, call, eval_env)
        elif method == "addImage":
            facts.element_types["image"] = facts.element_types.get("image", 0) + 1
        elif method == "addChart":
            facts.element_types["chart"] = facts.element_types.get("chart", 0) + 1
        elif method == "addTable":
            facts.element_types["table"] = facts.element_types.get("table", 0) + 1

    def _handle_background_assignment(facts: SlideFacts, expr, eval_env: EvalEnv):
        props = _extract_object_properties_with_env(expr.right, eval_env)
        if props.get("path") or props.get("data"):
            facts.background_kind = "image"
        elif props.get("color") or props.get("fill"):
            facts.background_kind = "solid"

    def _build_helper_env(params, call_args, caller_eval_env):
        env: EvalEnv = dict(caller_eval_env)
        for i, param in enumerate(params):
            if i >= len(call_args):
                break
            arg = call_args[i]
            if param.type == "Identifier":
                if arg.type == "ObjectExpression":
                    arg_props = _extract_object_properties_with_env(arg, caller_eval_env)
                    env[param.name] = arg_props
                else:
                    val = _resolve_node(arg, caller_eval_env)
                    if val is not None:
                        env[param.name] = val
            elif param.type == "ObjectPattern":
                if arg.type == "ObjectExpression":
                    arg_props = _extract_object_properties_with_env(arg, caller_eval_env)
                    for prop in param.properties:
                        if prop.type == "Property":
                            key = (prop.key.name if prop.key.type == "Identifier"
                                   else prop.key.value)
                            if key in arg_props:
                                env[key] = arg_props[key]
        return env

    def _handle_call(call, slide_bindings, eval_env):
        callee = call.callee
        if callee.type == "MemberExpression" and callee.object.type == "Identifier":
            var_name = callee.object.name
            facts = slide_bindings.get(var_name)
            if facts is None:
                return None
            method = callee.property.name if callee.property.type == "Identifier" else None
            if method:
                _apply_method(facts, method, call, eval_env)
            return facts

        if callee.type == "Identifier" and callee.name in helpers:
            if not call.arguments:
                return None
            first_arg = call.arguments[0]
            if first_arg.type != "Identifier":
                return None
            facts = slide_bindings.get(first_arg.name)
            if facts is None:
                return None
            params, body = helpers[callee.name]
            helper_env = _build_helper_env(params[1:], call.arguments[1:], eval_env)
            helper_param_name = (params[0].name if params and params[0].type == "Identifier"
                                  else None)
            helper_slide_bindings = dict(slide_bindings)
            if helper_param_name and helper_param_name not in helper_slide_bindings:
                helper_slide_bindings[helper_param_name] = facts
            _walk_body(body, helper_slide_bindings, helper_env, is_block_scope=False)
            return facts

        return None

    def _walk_body(body, outer_slide_bindings, eval_env, *, is_block_scope=False):
        slide_bindings = dict(outer_slide_bindings) if is_block_scope else outer_slide_bindings
        local_eval_env = dict(eval_env)
        for n in body:
            if n is None:
                continue
            if n.type == "VariableDeclaration":
                for decl in n.declarations:
                    init = decl.init
                    if (init and init.type == "CallExpression"
                            and _is_add_slide_call(init)):
                        sf = _new_slide()
                        if decl.id.type == "Identifier":
                            slide_bindings[decl.id.name] = sf
                    elif init is not None and decl.id.type == "Identifier":
                        val = _resolve_node(init, local_eval_env)
                        if val is not None:
                            local_eval_env[decl.id.name] = val
                    elif init is not None and decl.id.type == "ObjectPattern":
                        rhs = _resolve_node(init, local_eval_env)
                        if isinstance(rhs, dict):
                            for prop in decl.id.properties:
                                if prop.type == "Property":
                                    key = (prop.key.name if prop.key.type == "Identifier"
                                           else prop.key.value)
                                    if key in rhs:
                                        local_eval_env[key] = rhs[key]
                        elif init.type == "ObjectExpression":
                            arg_props = _extract_object_properties_with_env(init, local_eval_env)
                            for prop in decl.id.properties:
                                if prop.type == "Property":
                                    key = (prop.key.name if prop.key.type == "Identifier"
                                           else prop.key.value)
                                    if key in arg_props:
                                        local_eval_env[key] = arg_props[key]
                continue
            if n.type == "BlockStatement":
                _walk_body(n.body, slide_bindings, local_eval_env, is_block_scope=True)
                continue
            if n.type == "ExpressionStatement":
                expr = n.expression
                if expr.type == "CallExpression":
                    _handle_call(expr, slide_bindings, local_eval_env)
                elif expr.type == "AssignmentExpression":
                    lhs = expr.left
                    if (lhs.type == "MemberExpression"
                            and lhs.object.type == "Identifier"
                            and lhs.property.type == "Identifier"
                            and lhs.property.name == "background"):
                        facts = slide_bindings.get(lhs.object.name)
                        if facts is not None:
                            _handle_background_assignment(facts, expr, local_eval_env)
                continue
            if n.type == "IfStatement":
                if n.consequent:
                    inner = getattr(n.consequent, "body", None)
                    if isinstance(inner, list):
                        _walk_body(inner, slide_bindings, local_eval_env)
                    elif n.consequent.type == "ExpressionStatement":
                        expr = n.consequent.expression
                        if expr.type == "CallExpression":
                            _handle_call(expr, slide_bindings, local_eval_env)
                if n.alternate:
                    inner = getattr(n.alternate, "body", None)
                    if isinstance(inner, list):
                        _walk_body(inner, slide_bindings, local_eval_env)
                continue
            inner = getattr(n, "body", None)
            if isinstance(inner, list):
                _walk_body(inner, slide_bindings, local_eval_env)

    _walk_body(tree.body, {}, {})
    return slides_list
