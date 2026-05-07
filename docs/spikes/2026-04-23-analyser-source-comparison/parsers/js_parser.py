"""Parse a PptxGenJS build.js → list[SlideFacts] via esprima AST.

Strategy:
  1. One AST walk to collect top-level function declarations (helpers).
  2. One AST walk to walk statements in order, maintaining:
     - slide_bindings: var-name → SlideFacts (which slide variable is live)
     - eval_env: var-name → Python scalar (for resolving identifiers to values)

Block-scope handling (critical for Variant A):
  Variant A places each slide in its own block `{ const s = pres.addSlide(); ... }`.
  All 10 blocks use the same variable name `s`. We handle this by entering a
  fresh scope for each BlockStatement so that the `s` in each block maps to a
  newly created SlideFacts and doesn't collide with siblings.

Helper resolution:
  When a helper function is called (e.g. addMarker(s, "BG:foo", {x:0,...})):
  - The first argument is the slide variable.
  - The second argument (marker name string) and third (opts object) are evaluated
    at the call site and passed into the helper via eval_env keyed by param name.
  - For destructured object params ({x,y,w,h,...}), each destructured key is
    individually added to eval_env.
  - Inside the helper body, `objectName: marker` resolves because `marker` is now
    in eval_env; similarly `x/y/w/h` resolve for EMU conversion.
  - A local variable declared inside a helper (e.g. const name = `IMAGE:${slug}`)
    is evaluated and added to eval_env for subsequent use in that helper scope.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional, Union

import esprima

from slide_facts import Marker, SlideFacts

MARKER_RE = re.compile(r"^(IMAGE|SMARTART|BG):([A-Za-z0-9_-]+)$")
EMU_PER_INCH = 914400

# Type aliases
EvalEnv = dict[str, Any]   # identifier name → Python scalar value
SlideBindings = dict[str, SlideFacts]  # identifier name → SlideFacts


# ---------------------------------------------------------------------------
# AST value extraction
# ---------------------------------------------------------------------------

def _resolve_node(node, eval_env: EvalEnv) -> Any:
    """Try to evaluate an AST expression node to a Python scalar.

    Returns None when the expression is not statically resolvable.
    """
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
        # Only resolve if all expressions are resolvable.
        # quasi.value is an esprima TemplateElement.Value object — use attribute access.
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
    """Extract properties from an ObjectExpression, resolving identifiers via eval_env."""
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


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_js(path: Union[str, Path]) -> list[SlideFacts]:
    source = Path(path).read_text()
    tree = esprima.parseScript(source, options={"tolerant": True})

    # ------------------------------------------------------------------ #
    # Pass 1: collect top-level function declarations.                     #
    # Each entry: name → (params list of AST param nodes, body statements) #
    # ------------------------------------------------------------------ #
    helpers: dict[str, tuple[list, list]] = {}
    for stmt in tree.body:
        if stmt.type == "FunctionDeclaration" and stmt.params:
            helpers[stmt.id.name] = (stmt.params, stmt.body.body)

    # Ordered output list.
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

    # ------------------------------------------------------------------ #
    # Method handlers                                                      #
    # ------------------------------------------------------------------ #

    def _handle_add_text(facts: SlideFacts, call, eval_env: EvalEnv):
        if not call.arguments:
            return
        arg0 = call.arguments[0]
        val = _resolve_node(arg0, eval_env)
        if isinstance(val, str):
            facts.text_content = (facts.text_content + "\n" + val).strip()
            return
        # Array of run objects: [{text: "..."}, ...] or plain strings
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
            m = MARKER_RE.match(object_name)
            if m:
                facts.markers.append(Marker(
                    kind=m.group(1),
                    identifier=m.group(2),
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

    # ------------------------------------------------------------------ #
    # Build eval_env from a helper call's arguments                        #
    # ------------------------------------------------------------------ #

    def _build_helper_env(params: list, call_args: list, caller_eval_env: EvalEnv) -> EvalEnv:
        """Bind helper params to call-site argument values.

        Handles:
          - Identifier param receiving a scalar arg → resolved scalar stored in env
          - Identifier param receiving an ObjectExpression arg → the prop dict is
            stored in env under the param name (so `const {x,y} = opts` can later
            destructure it inside the helper body)
          - ObjectPattern param ({x, y, w, h, ...}) → each key gets the
            value extracted from the call arg ObjectExpression directly

        The resulting env is used inside the helper body so identifiers like
        `marker`, `x`, `y`, `w`, `h`, `slug` resolve to concrete call-site values.
        """
        env: EvalEnv = dict(caller_eval_env)
        for i, param in enumerate(params):
            if i >= len(call_args):
                break
            arg = call_args[i]
            if param.type == "Identifier":
                if arg.type == "ObjectExpression":
                    # Store the props dict so inner destructuring can access it.
                    arg_props = _extract_object_properties_with_env(arg, caller_eval_env)
                    env[param.name] = arg_props
                else:
                    val = _resolve_node(arg, caller_eval_env)
                    if val is not None:
                        env[param.name] = val
            elif param.type == "ObjectPattern":
                # Destructured: {x, y, w, h} = arg — bind each key directly
                if arg.type == "ObjectExpression":
                    arg_props = _extract_object_properties_with_env(arg, caller_eval_env)
                    for prop in param.properties:
                        if prop.type == "Property":
                            key = prop.key.name if prop.key.type == "Identifier" else prop.key.value
                            if key in arg_props:
                                env[key] = arg_props[key]
        return env

    # ------------------------------------------------------------------ #
    # Statement walker                                                     #
    # ------------------------------------------------------------------ #

    def _handle_call(
        call,
        slide_bindings: SlideBindings,
        eval_env: EvalEnv,
    ) -> Optional[SlideFacts]:
        """Process a CallExpression. Returns the resolved SlideFacts if one was created."""
        callee = call.callee

        # Direct method call on a slide variable: slide.addX(...)
        if callee.type == "MemberExpression" and callee.object.type == "Identifier":
            var_name = callee.object.name
            facts = slide_bindings.get(var_name)
            if facts is None:
                return None
            method = callee.property.name if callee.property.type == "Identifier" else None
            if method:
                _apply_method(facts, method, call, eval_env)
            return facts

        # Helper function call: helperName(slide, arg1, ...)
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
            # Build the helper's eval environment from the call arguments,
            # skipping the first (slide) param which is already resolved.
            helper_env = _build_helper_env(params[1:], call.arguments[1:], eval_env)
            # Bind the helper's first parameter name (e.g. "slide") to the same
            # SlideFacts so that `slide.addShape(...)` inside the helper resolves.
            helper_param_name = params[0].name if params and params[0].type == "Identifier" else None
            helper_slide_bindings = dict(slide_bindings)
            if helper_param_name and helper_param_name not in helper_slide_bindings:
                helper_slide_bindings[helper_param_name] = facts
            _walk_body(body, helper_slide_bindings, helper_env, is_block_scope=False)
            return facts

        return None

    def _walk_body(
        body: list,
        outer_slide_bindings: SlideBindings,
        eval_env: EvalEnv,
        *,
        is_block_scope: bool = False,
    ):
        """Walk a list of AST statements.

        Args:
            body: list of AST statement nodes
            outer_slide_bindings: var-name → SlideFacts from the enclosing scope
            eval_env: scalar value environment (for resolving identifiers)
            is_block_scope: when True, new slide bindings stay local to this
                block (sibling blocks with the same var name each get their own
                SlideFacts).
        """
        # Copy for block isolation; mutations inside don't affect the outer scope.
        slide_bindings = dict(outer_slide_bindings) if is_block_scope else outer_slide_bindings
        # eval_env is also copied per scope to avoid leaking helper locals
        local_eval_env = dict(eval_env)

        for n in body:
            if n is None:
                continue

            if n.type == "VariableDeclaration":
                for decl in n.declarations:
                    init = decl.init
                    if (init and init.type == "CallExpression"
                            and _is_add_slide_call(init)):
                        # New slide
                        sf = _new_slide()
                        if decl.id.type == "Identifier":
                            slide_bindings[decl.id.name] = sf
                    elif init is not None and decl.id.type == "Identifier":
                        # Local variable — try to evaluate and add to env
                        val = _resolve_node(init, local_eval_env)
                        if val is not None:
                            local_eval_env[decl.id.name] = val
                    elif init is not None and decl.id.type == "ObjectPattern":
                        # Destructuring: const {x, y, slug} = opts
                        # Resolve the RHS: could be an Identifier pointing to a dict in env
                        rhs = _resolve_node(init, local_eval_env)
                        if isinstance(rhs, dict):
                            # rhs is a props dict stored in env by _build_helper_env
                            for prop in decl.id.properties:
                                if prop.type == "Property":
                                    key = (prop.key.name if prop.key.type == "Identifier"
                                           else prop.key.value)
                                    if key in rhs:
                                        local_eval_env[key] = rhs[key]
                        elif init.type == "ObjectExpression":
                            # Inline destructuring: const {x,y} = {x:1, y:2}
                            arg_props = _extract_object_properties_with_env(init, local_eval_env)
                            for prop in decl.id.properties:
                                if prop.type == "Property":
                                    key = (prop.key.name if prop.key.type == "Identifier"
                                           else prop.key.value)
                                    if key in arg_props:
                                        local_eval_env[key] = arg_props[key]
                continue

            if n.type == "BlockStatement":
                # Enter a fresh block scope so repeated `const s = addSlide()`
                # in sibling blocks each maps to a distinct SlideFacts.
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
                # Descend into consequent/alternate (helper bodies may have if-label checks)
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

            # ForEachStatement, ForInStatement etc. — descend generically
            inner = getattr(n, "body", None)
            if isinstance(inner, list):
                _walk_body(inner, slide_bindings, local_eval_env)

    # ------------------------------------------------------------------ #
    # Pass 2: walk the top-level body.                                     #
    # ------------------------------------------------------------------ #
    _walk_body(tree.body, {}, {})

    # ------------------------------------------------------------------ #
    # Post-walk: tally text element counts.                                #
    # ------------------------------------------------------------------ #
    for facts in slides_list:
        if facts.text_content:
            facts.element_types["text"] = (
                facts.element_types.get("text", 0)
                + facts.text_content.count("\n") + 1
            )

    return slides_list


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) != 2:
        print("usage: js_parser.py <path.js>", file=sys.stderr)
        sys.exit(2)
    facts = parse_js(sys.argv[1])
    print(json.dumps([f.to_dict() for f in facts], indent=2))
