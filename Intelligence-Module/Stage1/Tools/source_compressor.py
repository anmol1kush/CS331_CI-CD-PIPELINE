"""
Source Compressor for Stage-1.

Builds a compressed, LLM-readable representation of source code
from semantic features extracted by Stage1_Semantic.py.

Usage:
    Iteration 0: full source code sent to LLM
    Iteration 1+: compressed representation replaces raw source code

The compressed output preserves enough structural information
for the LLM to generate meaningful tests without re-reading
the full source code.

Two layers:
    Layer 1 — Code structure (from semantic engine, deterministic)
    Layer 2 — Constraint context (from user_context, optional, free-form)

Consumers:
    - llm_test_generator.py (iteration 1+ prompts)
    - NOT used by Oracle_Verifier (handled separately in Task 13)
"""


class Source_Compressor:
    def __init__(self, structural_features, execution_model, language,
                 user_context=None):
        """
        Args:
            structural_features: dict from Stage1_Semantic.py
            execution_model: "callable_method" | "stdin_program" | "script"
            language: "python" | "c" | "cpp" | "java"
            user_context: optional free-form string with constraints/hints
        """
        self.features = structural_features or {}
        self.execution_model = execution_model
        self.language = language
        self.user_context = user_context

    def compress(self):
        """
        Produce the full compressed representation as a single string.
        """
        sections = []

        sections.append(self.build_header())
        sections.append(self.build_constraint_context())
        sections.append(self.build_input_characteristics())
        sections.append(self.build_entry_points())
        sections.append(self.build_signatures())
        sections.append(self.build_class_hierarchy())
        sections.append(self.build_control_flow())
        sections.append(self.build_loop_structure())
        sections.append(self.build_return_patterns())
        sections.append(self.build_exception_handling())
        sections.append(self.build_recursion_info())
        sections.append(self.build_complexity_summary())

        # Filter out empty sections
        sections = [s for s in sections if s]

        return "\n\n".join(sections)

    def build_header(self):
        """Language, execution model, basic stats."""
        line_count = self.features.get("line_count", 0)
        func_count = self.features.get("function_count", 0)
        class_count = self.features.get("class_count", 0)
        branch_count = self.features.get("branching_factor", 0)

        return (
            f"Language: {self.language}\n"
            f"Execution Model: {self.execution_model}\n"
            f"Structure: {line_count} lines, {func_count} functions, "
            f"{class_count} classes, {branch_count} branches"
        )

    def build_entry_points(self):
        """What's testable in this code."""
        entry_points = self.features.get("entry_points", [])
        if not entry_points:
            return ""

        lines = ["Entry Points:"]
        for ep in entry_points:
            ep_type = ep.get("type", "unknown")
            name = ep.get("name", "?")

            if ep_type == "class":
                methods = ep.get("public_methods", [])
                methods_str = ", ".join(methods) if methods else "none"
                lines.append(f"  class {name} → public methods: {methods_str}")
            elif ep_type == "function":
                lines.append(f"  function {name}()")
            elif ep_type == "main_block":
                lines.append(f"  __main__ block at L{ep.get('line', '?')}")

        return "\n".join(lines)

    def build_signatures(self):
        """Method/function signatures with params and annotations."""
        signatures = self.features.get("method_signatures", [])
        if not signatures:
            return ""

        lines = ["Signatures:"]
        for sig in signatures:
            name = sig.get("name", "?")
            params = sig.get("params", [])
            ret = sig.get("return_annotation")
            decorators = sig.get("decorators", [])
            is_async = sig.get("is_async", False)
            parent = sig.get("parent_class")

            # Build param string
            param_parts = []
            for p in params:
                if p["name"] == "self" or p["name"] == "cls":
                    continue
                ann = p.get("annotation")
                if ann:
                    param_parts.append(f"{p['name']}: {ann}")
                else:
                    param_parts.append(p["name"])
            param_str = ", ".join(param_parts)

            # Build prefix
            prefix = "  "
            if parent:
                prefix += f"{parent}."
            if is_async:
                prefix += "async "

            # Build decorator string
            dec_str = ""
            if decorators:
                dec_str = f" [{', '.join(decorators)}]"

            # Build return string
            ret_str = f" → {ret}" if ret else ""

            lines.append(f"{prefix}{name}({param_str}){ret_str}{dec_str}")

        return "\n".join(lines)

    def build_class_hierarchy(self):
        """Class inheritance and init params."""
        classes = self.features.get("class_hierarchy", [])
        if not classes:
            return ""

        lines = ["Class Hierarchy:"]
        for cls in classes:
            name = cls.get("name", "?")
            bases = cls.get("bases", [])
            init_params = cls.get("init_params", [])
            methods = cls.get("methods", [])

            base_str = f"({', '.join(bases)})" if bases else ""
            lines.append(f"  class {name}{base_str}:")

            if init_params:
                param_parts = []
                for p in init_params:
                    ann = p.get("annotation")
                    if ann:
                        param_parts.append(f"{p['name']}: {ann}")
                    else:
                        param_parts.append(p["name"])
                lines.append(f"    __init__({', '.join(param_parts)})")

            public = [m["name"] for m in methods if m.get("is_public")]
            private = [m["name"] for m in methods if not m.get("is_public")]

            if public:
                lines.append(f"    public: {', '.join(public)}")
            if private:
                lines.append(f"    private: {', '.join(private)}")

        return "\n".join(lines)

    def build_control_flow(self):
        """Branch conditions with line numbers."""
        conditions = self.features.get("branch_conditions", [])
        if not conditions:
            return ""

        lines = ["Control Flow:"]
        for cond in conditions:
            line = cond.get("line", "?")
            expr = cond.get("condition", "?")
            has_else = cond.get("has_else", False)
            has_elif = cond.get("has_elif", False)

            suffix = ""
            if has_elif:
                suffix = " [has elif]"
            elif has_else:
                suffix = " [has else]"

            lines.append(f"  L{line}: if {expr}{suffix}")

        return "\n".join(lines)

    def build_loop_structure(self):
        """Loop bounds and iteration patterns."""
        loops = self.features.get("loop_bounds", [])
        if not loops:
            return ""

        lines = ["Loops:"]
        for loop in loops:
            line = loop.get("line", "?")
            loop_type = loop.get("type", "?")

            if loop_type in ("for", "async_for"):
                target = loop.get("target") or "?"
                iterator = loop.get("iterator") or "?"
                prefix = "async for" if loop_type == "async_for" else "for"
                lines.append(f"  L{line}: {prefix} {target} in {iterator}")
            elif loop_type == "while":
                condition = loop.get("condition") or "?"
                lines.append(f"  L{line}: while {condition}")

        return "\n".join(lines)

    def build_return_patterns(self):
        """Per-function return points and expressions."""
        patterns = self.features.get("return_patterns", [])
        if not patterns:
            return ""

        lines = ["Returns:"]
        for pat in patterns:
            name = pat.get("function", "?")
            count = pat.get("return_count", 0)
            implicit = pat.get("implicit_none", False)
            returns = pat.get("returns", [])

            if count == 0 and implicit:
                lines.append(f"  {name} → None (implicit)")
            elif count == 1:
                val = returns[0]["value"] if returns else "?"
                lines.append(f"  {name} → {val}")
            else:
                return_vals = [r["value"] for r in returns]
                # Deduplicate for readability
                unique_vals = list(dict.fromkeys(return_vals))
                lines.append(f"  {name} → {count} paths: {', '.join(unique_vals)}")

        return "\n".join(lines)

    def build_exception_handling(self):
        """Try/except structure with exception types."""
        blocks = self.features.get("exception_blocks", [])
        if not blocks:
            return ""

        lines = ["Exception Handling:"]
        for block in blocks:
            line = block.get("line", "?")
            has_finally = block.get("has_finally", False)
            handlers = block.get("handlers", [])

            handler_strs = []
            for h in handlers:
                exc_type = h.get("type")
                if exc_type is None:
                    handler_strs.append("bare except")
                elif isinstance(exc_type, list):
                    handler_strs.append(f"except ({', '.join(exc_type)})")
                else:
                    handler_strs.append(f"except {exc_type}")

            suffix = " + finally" if has_finally else ""
            lines.append(f"  L{line}: try → {', '.join(handler_strs)}{suffix}")

        return "\n".join(lines)

    def build_recursion_info(self):
        """Recursion detection summary."""
        direct = self.features.get("direct_recursion", False)
        mutual = self.features.get("mutual_recursion", False)
        cycles = self.features.get("recursion_cycles", [])

        if not direct and not mutual:
            return ""

        lines = ["Recursion:"]
        if direct:
            direct_funcs = [c[0] for c in cycles if len(c) == 2]
            if direct_funcs:
                lines.append(f"  Direct: {', '.join(direct_funcs)}")
            else:
                lines.append("  Direct recursion detected")
        if mutual:
            mutual_chains = [c for c in cycles if len(c) > 2]
            for chain in mutual_chains:
                lines.append(f"  Mutual: {' → '.join(chain)}")

        return "\n".join(lines)

    def build_complexity_summary(self):
        """Cyclomatic complexity per function."""
        complexity = self.features.get("cyclomatic_complexity", [])
        if not complexity:
            return ""

        # Only include functions with non-trivial complexity
        notable = [c for c in complexity if c.get("complexity", 1) > 2]
        if not notable:
            return ""

        lines = ["Complexity:"]
        for c in sorted(notable, key=lambda x: x["complexity"], reverse=True):
            name = c.get("function", "?")
            val = c.get("complexity", 0)
            lines.append(f"  {name}: cyclomatic = {val}")

        return "\n".join(lines)

    def build_constraint_context(self):
        """
        User-provided constraints and hints.
        Free-form text placed in a dedicated prominent section.
        """
        if not self.user_context or not self.user_context.strip():
            return ""

        return (
            "Constraints & Context (developer-provided):\n"
            f"  {self.user_context.strip()}"
        )

    def build_input_characteristics(self):
        """
        Auto-derive input type, nullability, size, and value hints
        from semantic features. No user input required.
        """
        signatures = self.features.get("method_signatures", [])
        conditions = self.features.get("branch_conditions", [])
        loops = self.features.get("loop_bounds", [])

        if not signatures:
            return ""

        characteristics = []

        for sig in signatures:
            # Skip private/dunder methods except __init__
            name = sig.get("name", "")
            if name.startswith("_") and name != "__init__":
                continue

            params = sig.get("params", [])
            for param in params:
                pname = param.get("name", "")
                if pname in ("self", "cls"):
                    continue

                traits = []

                # 1. Type from annotation
                ann = param.get("annotation")
                if ann:
                    traits.append(f"type: {ann}")

                    # Infer nullability from Optional/None in annotation
                    if "Optional" in ann or "None" in ann:
                        traits.append("nullable")

                # 2. Nullability from branch conditions
                for cond in conditions:
                    expr = cond.get("condition", "")
                    if pname in expr and ("is None" in expr or "is not None" in expr
                                          or "not " + pname in expr
                                          or pname + " is None" in expr):
                        if "nullable" not in traits:
                            traits.append("nullable")
                        break

                # 3. Size/iteration hints from loop bounds
                for loop in loops:
                    iterator = loop.get("iterator") or ""
                    target = loop.get("target") or ""
                    condition = loop.get("condition") or ""

                    # Parameter used as iterator → likely collection
                    if pname in iterator or pname == iterator:
                        traits.append("iterable")
                    # range(len(param)) pattern → sized collection
                    if f"len({pname})" in iterator or f"len({pname})" in condition:
                        traits.append("sized collection")
                    # range(param) → integer bound
                    if f"range({pname})" in iterator:
                        traits.append("integer (used as bound)")

                # 4. Method calls on parameter → infer type
                for cond in conditions:
                    expr = cond.get("condition", "")
                    if f"{pname}.val" in expr or f"{pname}.next" in expr:
                        traits.append("linked structure (has .val/.next)")
                        break
                    if f"{pname}.left" in expr or f"{pname}.right" in expr:
                        traits.append("tree node (has .left/.right)")
                        break

                # 5. Value range hints from comparisons
                for cond in conditions:
                    expr = cond.get("condition", "")
                    if pname in expr:
                        if "< 0" in expr or "<= 0" in expr or "> 0" in expr or ">= 0" in expr:
                            traits.append("may be negative/zero")
                        if "== 0" in expr:
                            traits.append("zero is a boundary case")

                if traits:
                    characteristics.append(f"  {pname}: {', '.join(traits)}")

        if not characteristics:
            return ""

        return "Input Characteristics:\n" + "\n".join(characteristics)