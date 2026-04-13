"""
Java Parser — tree-sitter based implementation of ParserBase.

Uses tree-sitter-java grammar.
"""

import tree_sitter_java as ts_java
from tree_sitter import Language, Parser
from Stage1.Parsers.parser_base import ParserBase


FUNCTION_TYPES = {"method_declaration", "constructor_declaration"}
CLASS_TYPES = {"class_declaration", "interface_declaration", "enum_declaration"}
LOOP_TYPES = {"for_statement", "enhanced_for_statement", "while_statement", "do_statement"}
BRANCH_TYPES = {"if_statement", "switch_expression", "ternary_expression"}


class JavaParser(ParserBase):

    def __init__(self, source_code: str):
        super().__init__(source_code, "java")
        self._parser = Parser()
        lang = Language(ts_java.language())
        self._parser.language = lang

    def parse(self) -> bool:
        try:
            self.tree = self._parser.parse(self.source_code.encode("utf-8"))
            return self.tree is not None and self.tree.root_node is not None
        except Exception:
            self.tree = None
            return False

    # ── Helpers ──

    def _walk(self, node=None):
        if node is None:
            if not self.tree:
                return
            node = self.tree.root_node
        yield node
        for child in node.children:
            yield from self._walk(child)

    def _node_text(self, node) -> str:
        return node.text.decode("utf-8") if node.text else ""

    def _find_name(self, node) -> str:
        for child in node.children:
            if child.type == "identifier":
                return self._node_text(child)
        return "<unknown>"

    def _has_modifier(self, node, modifier: str) -> bool:
        for child in node.children:
            if child.type == "modifiers":
                return modifier in self._node_text(child)
        return False

    # ── Structural Summary ──

    def extract_structural_summary(self) -> dict:
        if not self.tree:
            return self.empty_summary()

        functions = 0
        classes = 0
        loops = 0
        branches = 0
        max_depth = 0

        for node in self._walk():
            depth = 0
            current = node
            while current.parent:
                current = current.parent
                depth += 1
            max_depth = max(max_depth, depth)

            if node.type in FUNCTION_TYPES:
                functions += 1
            if node.type in CLASS_TYPES:
                classes += 1
            if node.type in LOOP_TYPES:
                loops += 1
            if node.type in BRANCH_TYPES:
                branches += 1

        call_graph = self.build_call_graph()
        recursion_info = self.detect_recursion(call_graph)

        return {
            "function_count": functions,
            "class_count": classes,
            "loop_count": loops,
            "max_nesting_depth": max_depth,
            "branching_factor": branches,
            "line_count": len(self.source_code.splitlines()) if self.source_code else 0,
            "executable_lines": self.get_executable_lines(),
            "recursiondetected": recursion_info["direct_recursion"] or recursion_info["mutual_recursion"],
            "direct_recursion": recursion_info["direct_recursion"],
            "mutual_recursion": recursion_info["mutual_recursion"],
            "recursion_cycles": recursion_info["cycles"]
        }

    # ── Method Signatures ──

    def extract_method_signatures(self) -> list:
        if not self.tree:
            return []

        signatures = []
        for node in self._walk():
            if node.type not in FUNCTION_TYPES:
                continue

            name = self._find_name(node)
            is_static = self._has_modifier(node, "static")

            # Extract parameters
            params = []
            for child in node.children:
                if child.type == "formal_parameters":
                    for param_node in child.children:
                        if param_node.type == "formal_parameter":
                            param_name = ""
                            param_type = ""
                            for pc in param_node.children:
                                if pc.type == "identifier":
                                    param_name = self._node_text(pc)
                                elif pc.type in ("type_identifier", "integral_type",
                                                 "floating_point_type", "boolean_type",
                                                 "array_type", "generic_type"):
                                    param_type = self._node_text(pc)
                            params.append({
                                "name": param_name,
                                "annotation": param_type if param_type else None
                            })

            # Return type
            return_type = None
            for child in node.children:
                if child.type in ("type_identifier", "integral_type", "void_type",
                                  "floating_point_type", "boolean_type", "generic_type",
                                  "array_type"):
                    return_type = self._node_text(child)
                    break

            # Parent class
            parent_class = None
            parent = node.parent
            while parent:
                if parent.type in CLASS_TYPES:
                    parent_class = self._find_name(parent)
                    break
                parent = parent.parent

            signatures.append({
                "name": name,
                "line": node.start_point[0] + 1,
                "is_async": False,
                "params": params,
                "defaults": [],
                "return_annotation": return_type,
                "decorators": [],
                "is_static": is_static,
                "is_classmethod": False,
                "is_property": False,
                "parent_class": parent_class
            })

        return signatures

    # ── Branch Conditions ──

    def extract_branch_conditions(self) -> list:
        if not self.tree:
            return []

        conditions = []
        for node in self._walk():
            if node.type == "if_statement":
                condition_node = None
                has_else = False
                has_elif = False

                for child in node.children:
                    if child.type == "parenthesized_expression":
                        condition_node = child
                    if child.type == "else" or (child.type == "block" and
                            any(c.type == "if_statement" for c in node.children)):
                        pass

                # Check for else/elif by looking at children
                children_types = [c.type for c in node.children]
                if "else" in self._node_text(node):
                    has_else = True
                # Simplified: check if last child is if_statement (elif pattern)
                non_trivial = [c for c in node.children if c.type not in ("if", "(", ")", "{", "}")]
                if len(non_trivial) >= 3 and non_trivial[-1].type == "if_statement":
                    has_elif = True

                conditions.append({
                    "line": node.start_point[0] + 1,
                    "condition": self._node_text(condition_node) if condition_node else "?",
                    "has_else": has_else,
                    "has_elif": has_elif
                })

        return conditions

    # ── Loop Bounds ──

    def extract_loop_bounds(self) -> list:
        if not self.tree:
            return []

        loops = []
        for node in self._walk():
            line = node.start_point[0] + 1

            if node.type == "for_statement":
                loops.append({
                    "type": "for",
                    "line": line,
                    "target": None,
                    "iterator": self._node_text(node),
                    "condition": None
                })
            elif node.type == "enhanced_for_statement":
                loops.append({
                    "type": "for_each",
                    "line": line,
                    "target": None,
                    "iterator": self._node_text(node),
                    "condition": None
                })
            elif node.type == "while_statement":
                cond = None
                for child in node.children:
                    if child.type == "parenthesized_expression":
                        cond = self._node_text(child)
                loops.append({
                    "type": "while",
                    "line": line,
                    "target": None,
                    "iterator": None,
                    "condition": cond or "?"
                })
            elif node.type == "do_statement":
                cond = None
                for child in node.children:
                    if child.type == "parenthesized_expression":
                        cond = self._node_text(child)
                loops.append({
                    "type": "do_while",
                    "line": line,
                    "target": None,
                    "iterator": None,
                    "condition": cond or "?"
                })

        return loops

    # ── Return Patterns ──

    def extract_return_patterns(self) -> list:
        if not self.tree:
            return []

        patterns = []
        for node in self._walk():
            if node.type not in FUNCTION_TYPES:
                continue

            name = self._find_name(node)
            returns = []

            for child in self._walk(node):
                if child.type == "return_statement":
                    val_parts = [c for c in child.children
                                 if c.type not in ("return", ";")]
                    val = self._node_text(val_parts[0]) if val_parts else "void"
                    returns.append({
                        "line": child.start_point[0] + 1,
                        "value": val
                    })

            # Check if return type is void
            is_void = False
            for child in node.children:
                if child.type == "void_type":
                    is_void = True

            patterns.append({
                "function": name,
                "line": node.start_point[0] + 1,
                "return_count": len(returns),
                "returns": returns,
                "implicit_none": is_void
            })

        return patterns

    # ── Class Hierarchy ──

    def extract_class_hierarchy(self) -> list:
        if not self.tree:
            return []

        classes = []
        for node in self._walk():
            if node.type not in CLASS_TYPES:
                continue

            name = self._find_name(node)
            bases = []
            methods = []
            init_params = []

            for child in node.children:
                if child.type == "superclass":
                    for c in child.children:
                        if c.type == "type_identifier":
                            bases.append(self._node_text(c))
                if child.type == "super_interfaces":
                    for c in child.children:
                        if c.type == "type_identifier":
                            bases.append(self._node_text(c))

                if child.type == "class_body":
                    for member in child.children:
                        if member.type in FUNCTION_TYPES:
                            m_name = self._find_name(member)
                            is_public = self._has_modifier(member, "public") or \
                                        not self._has_modifier(member, "private")
                            methods.append({
                                "name": m_name,
                                "line": member.start_point[0] + 1,
                                "is_public": is_public
                            })
                            # Constructor params
                            if member.type == "constructor_declaration":
                                for pc in member.children:
                                    if pc.type == "formal_parameters":
                                        for p in pc.children:
                                            if p.type == "formal_parameter":
                                                p_name = ""
                                                p_type = ""
                                                for pp in p.children:
                                                    if pp.type == "identifier":
                                                        p_name = self._node_text(pp)
                                                    elif pp.type in ("type_identifier", "integral_type"):
                                                        p_type = self._node_text(pp)
                                                init_params.append({
                                                    "name": p_name,
                                                    "annotation": p_type or None
                                                })

            classes.append({
                "name": name,
                "line": node.start_point[0] + 1,
                "bases": bases,
                "methods": methods,
                "init_params": init_params
            })

        return classes

    # ── Exception Blocks ──

    def extract_exception_blocks(self) -> list:
        if not self.tree:
            return []

        blocks = []
        for node in self._walk():
            if node.type == "try_statement" or node.type == "try_with_resources_statement":
                has_finally = False
                handlers = []

                for child in node.children:
                    if child.type == "catch_clause":
                        exc_type = None
                        for cc in child.children:
                            if cc.type == "catch_formal_parameter":
                                for ccp in cc.children:
                                    if ccp.type == "catch_type":
                                        exc_type = self._node_text(ccp)
                        handlers.append({
                            "type": exc_type,
                            "line": child.start_point[0] + 1
                        })
                    if child.type == "finally_clause":
                        has_finally = True

                blocks.append({
                    "line": node.start_point[0] + 1,
                    "has_finally": has_finally,
                    "has_else": False,
                    "handlers": handlers
                })

        return blocks

    # ── Assert Statements ──

    def extract_assert_statements(self) -> list:
        if not self.tree:
            return []

        asserts = []
        for node in self._walk():
            if node.type == "assert_statement":
                children = [c for c in node.children if c.type not in ("assert", ";", ":")]
                condition = self._node_text(children[0]) if children else "?"
                message = self._node_text(children[1]) if len(children) > 1 else None
                asserts.append({
                    "line": node.start_point[0] + 1,
                    "condition": condition,
                    "message": message
                })

        return asserts

    # ── Import Analysis ──

    def analyze_imports(self) -> list:
        if not self.tree:
            return []

        java_stdlib = {"java", "javax", "sun", "com.sun", "jdk", "org.w3c", "org.xml"}

        imports = []
        for node in self._walk():
            if node.type == "import_declaration":
                # Get the full import path
                for child in node.children:
                    if child.type == "scoped_identifier":
                        module = self._node_text(child)
                        root = module.split(".")[0]
                        imports.append({
                            "module": module,
                            "alias": None,
                            "names": None,
                            "line": node.start_point[0] + 1,
                            "category": "stdlib" if root in java_stdlib else "third_party"
                        })

        return imports

    # ── Async Patterns ──

    def detect_async_patterns(self) -> dict:
        """Java doesn't have native async/await. Return zeros."""
        return {
            "async_functions": 0,
            "await_count": 0,
            "async_for_count": 0,
            "async_with_count": 0,
            "is_async_code": False
        }

    # ── Entry Points ──

    def detect_entry_points(self) -> list:
        if not self.tree:
            return []

        entry_points = []
        for node in self._walk():
            if node.type in CLASS_TYPES:
                name = self._find_name(node)
                public_methods = []
                has_main = False

                for child in node.children:
                    if child.type == "class_body":
                        for member in child.children:
                            if member.type == "method_declaration":
                                m_name = self._find_name(member)
                                method_text = self._node_text(member)
                                if "public static void main" in method_text:
                                    has_main = True
                                if self._has_modifier(member, "public") and m_name != "main":
                                    public_methods.append(m_name)

                if has_main:
                    entry_points.append({
                        "type": "main_block",
                        "name": name,
                        "line": node.start_point[0] + 1,
                        "public_methods": None
                    })
                elif public_methods:
                    entry_points.append({
                        "type": "class",
                        "name": name,
                        "line": node.start_point[0] + 1,
                        "public_methods": public_methods
                    })

        return entry_points

    # ── Operation Vocabulary ──

    def extract_operation_vocabulary(self) -> list:
        if not self.tree:
            return []

        operations = set()

        for node in self._walk():
            if node.type == "method_invocation":
                for child in node.children:
                    if child.type == "identifier":
                        operations.add(("method", self._node_text(child)))
            elif node.type == "object_creation_expression":
                operations.add(("builtin_or_func", "new"))
                for child in node.children:
                    if child.type == "type_identifier":
                        operations.add(("builtin_or_func", self._node_text(child)))
            elif node.type == "binary_expression":
                for child in node.children:
                    text = self._node_text(child)
                    if text in ("+", "-", "*", "/", "%", "==", "!=", "<", ">",
                                "<=", ">=", "&&", "||", "&", "|", "^", "<<", ">>",
                                ">>>", "instanceof"):
                        operations.add(("operator", text))
            elif node.type == "unary_expression":
                for child in node.children:
                    text = self._node_text(child)
                    if text in ("!", "-", "+", "~", "++", "--"):
                        operations.add(("operator", text))
            elif node.type == "array_access":
                operations.add(("operator", "index"))
            elif node.type == "throw_statement":
                operations.add(("control", "throw"))
            elif node.type == "assert_statement":
                operations.add(("control", "assert"))

        return [{"category": cat, "name": name} for cat, name in sorted(operations)]

    # ── Cyclomatic Complexity ──

    def compute_cyclomatic_complexity(self) -> list:
        if not self.tree:
            return []

        results = []
        for node in self._walk():
            if node.type not in FUNCTION_TYPES:
                continue

            name = self._find_name(node)
            complexity = 1

            for child in self._walk(node):
                if child.type == "if_statement":
                    complexity += 1
                elif child.type in LOOP_TYPES:
                    complexity += 1
                elif child.type == "catch_clause":
                    complexity += 1
                elif child.type == "switch_expression_arm" or child.type == "switch_label":
                    complexity += 1
                elif child.type == "binary_expression":
                    for c in child.children:
                        if self._node_text(c) in ("&&", "||"):
                            complexity += 1
                elif child.type == "ternary_expression":
                    complexity += 1

            results.append({
                "function": name,
                "line": node.start_point[0] + 1,
                "complexity": complexity
            })

        return results

    # ── Call Graph ──

    def build_call_graph(self) -> dict:
        if not self.tree:
            return {}

        defined_methods = set()
        for node in self._walk():
            if node.type in FUNCTION_TYPES:
                defined_methods.add(self._find_name(node))

        call_graph = {}
        for node in self._walk():
            if node.type not in FUNCTION_TYPES:
                continue
            name = self._find_name(node)
            calls = set()
            for child in self._walk(node):
                if child.type == "method_invocation":
                    for c in child.children:
                        if c.type == "identifier":
                            callee = self._node_text(c)
                            if callee in defined_methods:
                                calls.add(callee)
            call_graph[name] = calls

        return call_graph

    # ── Global Variable Usage ──

    def detect_global_variable_usage(self) -> list:
        """Java has class-level fields, not global vars. Detect field access in methods."""
        if not self.tree:
            return []

        # Collect class field names
        fields = set()
        for node in self._walk():
            if node.type == "field_declaration":
                for child in node.children:
                    if child.type == "variable_declarator":
                        for c in child.children:
                            if c.type == "identifier":
                                fields.add(self._node_text(c))

        if not fields:
            return []

        usage = []
        for node in self._walk():
            if node.type not in FUNCTION_TYPES:
                continue

            name = self._find_name(node)
            referenced = set()
            for child in self._walk(node):
                if child.type == "identifier":
                    ident = self._node_text(child)
                    if ident in fields:
                        referenced.add(ident)

            if referenced:
                usage.append({
                    "function": name,
                    "line": node.start_point[0] + 1,
                    "declared_global": [],
                    "references_module_vars": list(referenced)
                })

        return usage

    # ── Comprehensions ──

    def count_comprehensions(self) -> dict:
        """Java has no comprehensions."""
        return {"list": 0, "dict": 0, "set": 0, "generator": 0}

    # ── Executable Lines ──

    def get_executable_lines(self) -> list:
        executable = set()
        if not self.source_code:
            return []

        in_block_comment = False
        for i, line in enumerate(self.source_code.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("/*"):
                in_block_comment = True
            if in_block_comment:
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("//"):
                continue
            executable.add(i)

        return list(executable)

    # ── Internal Helpers ──

    def detect_recursion(self, call_graph: dict) -> dict:
        visited = set()
        in_stack = set()
        cycles_found = []

        def dfs(func, path):
            visited.add(func)
            in_stack.add(func)
            path.append(func)

            for callee in call_graph.get(func, set()):
                if callee in in_stack:
                    cycle_start = path.index(callee)
                    cycles_found.append(path[cycle_start:] + [callee])
                elif callee not in visited:
                    dfs(callee, path)

            path.pop()
            in_stack.remove(func)

        for func in call_graph:
            if func not in visited:
                dfs(func, [])

        return {
            "direct_recursion": any(len(c) == 2 for c in cycles_found),
            "mutual_recursion": any(len(c) > 2 for c in cycles_found),
            "cycles": cycles_found
        }

    def empty_summary(self) -> dict:
        return {
            "function_count": 0, "class_count": 0, "loop_count": 0,
            "max_nesting_depth": 0, "branching_factor": 0, "line_count": 0,
            "executable_lines": [], "recursiondetected": False,
            "direct_recursion": False, "mutual_recursion": False,
            "recursion_cycles": []
        }