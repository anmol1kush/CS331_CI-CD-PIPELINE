"""
JavaScript/TypeScript Parser — tree-sitter based implementation of ParserBase.

Handles .js, .jsx, .ts, .tsx files.
Uses tree-sitter-javascript and tree-sitter-typescript grammars.

Note: JS and TS share most node types. The parser dispatches
to the correct grammar at parse time based on self.language.
"""

import tree_sitter_javascript as ts_js
import tree_sitter_typescript as ts_ts
from tree_sitter import Language, Parser
from Stage1.Parsers.parser_base import ParserBase


# Node types mapped to structural concepts
FUNCTION_TYPES = {"function_declaration", "function", "arrow_function",
                  "method_definition", "generator_function_declaration"}
CLASS_TYPES = {"class_declaration", "class"}
LOOP_TYPES = {"for_statement", "for_in_statement", "for_of_statement",
              "while_statement", "do_statement"}
BRANCH_TYPES = {"if_statement", "switch_case", "ternary_expression",
                "conditional_expression"}
TRY_TYPES = {"try_statement"}


class JSTSParser(ParserBase):

    def __init__(self, source_code: str, language: str = "javascript"):
        super().__init__(source_code, language)
        self._parser = Parser()

        if language == "typescript":
            lang = Language(ts_ts.language_typescript())
        else:
            lang = Language(ts_js.language())

        self._parser.language = lang

    def parse(self) -> bool:
        try:
            self.tree = self._parser.parse(self.source_code.encode("utf-8"))
            return self.tree is not None and self.tree.root_node is not None
        except Exception:
            self.tree = None
            return False

    # ── Tree Walking Helpers ──

    def _walk(self, node=None):
        """Yield all nodes in the tree via DFS."""
        if node is None:
            if not self.tree:
                return
            node = self.tree.root_node

        yield node
        for child in node.children:
            yield from self._walk(child)

    def _node_text(self, node) -> str:
        """Get source text for a node."""
        return node.text.decode("utf-8") if node.text else ""

    def _find_name(self, node) -> str:
        """Extract the name identifier from a function/class node."""
        for child in node.children:
            if child.type == "identifier":
                return self._node_text(child)
            if child.type == "property_identifier":
                return self._node_text(child)
        return "<anonymous>"

    def _get_depth(self, node) -> int:
        """Get nesting depth of a node."""
        depth = 0
        current = node
        while current.parent:
            current = current.parent
            depth += 1
        return depth

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
            depth = self._get_depth(node)
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
            is_async = any(
                child.type == "async" or self._node_text(child) == "async"
                for child in node.children
            )

            # Extract parameters
            params = []
            for child in node.children:
                if child.type == "formal_parameters":
                    for param_node in child.children:
                        if param_node.type in ("identifier", "required_parameter",
                                                "optional_parameter", "rest_pattern"):
                            param_name = self._node_text(param_node)
                            params.append({"name": param_name, "annotation": None})

            # Check for static keyword (class method context)
            is_static = any(
                self._node_text(child) == "static" for child in node.children
            )

            # Find parent class
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
                "is_async": is_async,
                "params": params,
                "defaults": [],
                "return_annotation": None,
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
                    if child.type == "else_clause":
                        has_else = True
                        # Check if else contains another if (elif)
                        for grandchild in child.children:
                            if grandchild.type == "if_statement":
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
            elif node.type in ("for_in_statement", "for_of_statement"):
                loop_type = "for_in" if node.type == "for_in_statement" else "for_of"
                left = right = None
                for child in node.children:
                    if child.type in ("identifier", "variable_declaration"):
                        left = self._node_text(child)
                    if child.type not in ("identifier", "variable_declaration",
                                          "for", "in", "of", "(", ")", "statement_block"):
                        right = self._node_text(child)
                loops.append({
                    "type": loop_type,
                    "line": line,
                    "target": left,
                    "iterator": right,
                    "condition": None
                })
            elif node.type == "while_statement":
                condition_node = None
                for child in node.children:
                    if child.type == "parenthesized_expression":
                        condition_node = child
                loops.append({
                    "type": "while",
                    "line": line,
                    "target": None,
                    "iterator": None,
                    "condition": self._node_text(condition_node) if condition_node else "?"
                })
            elif node.type == "do_statement":
                condition_node = None
                for child in node.children:
                    if child.type == "parenthesized_expression":
                        condition_node = child
                loops.append({
                    "type": "do_while",
                    "line": line,
                    "target": None,
                    "iterator": None,
                    "condition": self._node_text(condition_node) if condition_node else "?"
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
                    # Get return value (child after 'return' keyword)
                    val_parts = [c for c in child.children if c.type != "return"]
                    val = self._node_text(val_parts[0]) if val_parts else "undefined"
                    returns.append({
                        "line": child.start_point[0] + 1,
                        "value": val
                    })

            # Arrow functions with expression body = implicit return
            is_arrow = node.type == "arrow_function"
            has_explicit_return = len(returns) > 0

            patterns.append({
                "function": name,
                "line": node.start_point[0] + 1,
                "return_count": len(returns),
                "returns": returns,
                "implicit_none": not has_explicit_return and not is_arrow
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
                # extends clause
                if child.type == "class_heritage":
                    for heritage_child in child.children:
                        if heritage_child.type == "identifier":
                            bases.append(self._node_text(heritage_child))

                # class body
                if child.type == "class_body":
                    for member in child.children:
                        if member.type == "method_definition":
                            method_name = self._find_name(member)
                            is_public = not method_name.startswith("_") and not method_name.startswith("#")
                            methods.append({
                                "name": method_name,
                                "line": member.start_point[0] + 1,
                                "is_public": is_public
                            })

                            # Constructor params
                            if method_name == "constructor":
                                for param_child in member.children:
                                    if param_child.type == "formal_parameters":
                                        for p in param_child.children:
                                            if p.type in ("identifier", "required_parameter"):
                                                init_params.append({
                                                    "name": self._node_text(p),
                                                    "annotation": None
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
            if node.type == "try_statement":
                has_finally = False
                handlers = []

                for child in node.children:
                    if child.type == "catch_clause":
                        exc_type = None
                        for cc in child.children:
                            if cc.type == "identifier":
                                exc_type = self._node_text(cc)
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
        """JS doesn't have built-in assert syntax. Look for console.assert / assert() calls."""
        if not self.tree:
            return []

        asserts = []
        for node in self._walk():
            if node.type == "call_expression":
                func_text = ""
                for child in node.children:
                    if child.type in ("identifier", "member_expression"):
                        func_text = self._node_text(child)
                if "assert" in func_text.lower():
                    args = []
                    for child in node.children:
                        if child.type == "arguments":
                            args = [self._node_text(a) for a in child.children
                                    if a.type not in ("(", ")", ",")]
                    asserts.append({
                        "line": node.start_point[0] + 1,
                        "condition": args[0] if args else "?",
                        "message": args[1] if len(args) > 1 else None
                    })

        return asserts

    # ── Import Analysis ──

    def analyze_imports(self) -> list:
        if not self.tree:
            return []

        node_builtins = {"fs", "path", "http", "https", "url", "os", "crypto",
                         "stream", "util", "events", "child_process", "net",
                         "buffer", "querystring", "zlib", "cluster", "assert",
                         "readline", "tls", "dns", "dgram", "vm", "worker_threads"}

        imports = []
        for node in self._walk():
            if node.type == "import_statement":
                # ES6: import X from 'module'
                source = None
                names = []
                for child in node.children:
                    if child.type == "string":
                        source = self._node_text(child).strip("'\"")
                    if child.type in ("import_clause", "identifier", "namespace_import"):
                        names.append(self._node_text(child))

                if source:
                    root = source.split("/")[0].lstrip("@")
                    imports.append({
                        "module": source,
                        "alias": None,
                        "names": names,
                        "line": node.start_point[0] + 1,
                        "category": "stdlib" if root in node_builtins else
                                   ("local" if source.startswith(".") else "third_party")
                    })

            elif node.type == "call_expression":
                # CommonJS: require('module')
                func_text = ""
                for child in node.children:
                    if child.type == "identifier":
                        func_text = self._node_text(child)
                if func_text == "require":
                    for child in node.children:
                        if child.type == "arguments":
                            for arg in child.children:
                                if arg.type == "string":
                                    source = self._node_text(arg).strip("'\"")
                                    root = source.split("/")[0].lstrip("@")
                                    imports.append({
                                        "module": source,
                                        "alias": None,
                                        "names": None,
                                        "line": node.start_point[0] + 1,
                                        "category": "stdlib" if root in node_builtins else
                                                   ("local" if source.startswith(".") else "third_party")
                                    })

        return imports

    # ── Async Patterns ──

    def detect_async_patterns(self) -> dict:
        if not self.tree:
            return {"async_functions": 0, "await_count": 0, "async_for_count": 0,
                    "async_with_count": 0, "is_async_code": False}

        patterns = {"async_functions": 0, "await_count": 0,
                    "async_for_count": 0, "async_with_count": 0, "is_async_code": False}

        for node in self._walk():
            if node.type in FUNCTION_TYPES:
                if any(self._node_text(c) == "async" for c in node.children):
                    patterns["async_functions"] += 1
            if node.type == "await_expression":
                patterns["await_count"] += 1
            if node.type == "for_of_statement":
                # for await...of
                if any(self._node_text(c) == "await" for c in node.children):
                    patterns["async_for_count"] += 1

        patterns["is_async_code"] = (
            patterns["async_functions"] > 0 or patterns["await_count"] > 0
        )
        return patterns

    # ── Entry Points ──

    def detect_entry_points(self) -> list:
        if not self.tree:
            return []

        entry_points = []
        root = self.tree.root_node

        for node in root.children:
            if node.type == "function_declaration":
                name = self._find_name(node)
                if not name.startswith("_"):
                    entry_points.append({
                        "type": "function",
                        "name": name,
                        "line": node.start_point[0] + 1,
                        "public_methods": None
                    })

            elif node.type == "export_statement":
                for child in node.children:
                    if child.type == "function_declaration":
                        name = self._find_name(child)
                        entry_points.append({
                            "type": "function",
                            "name": name,
                            "line": child.start_point[0] + 1,
                            "public_methods": None
                        })
                    elif child.type in CLASS_TYPES:
                        name = self._find_name(child)
                        public_methods = []
                        for body_child in child.children:
                            if body_child.type == "class_body":
                                for member in body_child.children:
                                    if member.type == "method_definition":
                                        m_name = self._find_name(member)
                                        if not m_name.startswith("_") and m_name != "constructor":
                                            public_methods.append(m_name)
                        if public_methods:
                            entry_points.append({
                                "type": "class",
                                "name": name,
                                "line": child.start_point[0] + 1,
                                "public_methods": public_methods
                            })

            elif node.type in CLASS_TYPES:
                name = self._find_name(node)
                public_methods = []
                for child in node.children:
                    if child.type == "class_body":
                        for member in child.children:
                            if member.type == "method_definition":
                                m_name = self._find_name(member)
                                if not m_name.startswith("_") and m_name != "constructor":
                                    public_methods.append(m_name)
                if public_methods:
                    entry_points.append({
                        "type": "class",
                        "name": name,
                        "line": node.start_point[0] + 1,
                        "public_methods": public_methods
                    })

            # module.exports = ... pattern
            elif node.type == "expression_statement":
                text = self._node_text(node)
                if "module.exports" in text:
                    entry_points.append({
                        "type": "main_block",
                        "name": "module.exports",
                        "line": node.start_point[0] + 1,
                        "public_methods": None
                    })

        return entry_points

    # ── Operation Vocabulary ──

    def extract_operation_vocabulary(self) -> list:
        if not self.tree:
            return []

        operations = set()

        for node in self._walk():
            if node.type == "call_expression":
                for child in node.children:
                    if child.type == "identifier":
                        operations.add(("builtin_or_func", self._node_text(child)))
                    elif child.type == "member_expression":
                        for mc in child.children:
                            if mc.type == "property_identifier":
                                operations.add(("method", self._node_text(mc)))

            elif node.type == "binary_expression":
                for child in node.children:
                    if child.type in ("+", "-", "*", "/", "%", "**",
                                      "==", "===", "!=", "!==", "<", ">",
                                      "<=", ">=", "&&", "||", "??",
                                      "&", "|", "^", "<<", ">>", ">>>"):
                        operations.add(("operator", self._node_text(child)))

            elif node.type == "unary_expression":
                for child in node.children:
                    if child.type in ("!", "-", "+", "~", "typeof", "void", "delete"):
                        operations.add(("operator", self._node_text(child)))

            elif node.type == "subscript_expression":
                operations.add(("operator", "index"))

            elif node.type == "yield_expression":
                operations.add(("control", "yield"))

            elif node.type == "await_expression":
                operations.add(("control", "await"))

            elif node.type == "throw_statement":
                operations.add(("control", "throw"))

            elif node.type == "template_string":
                operations.add(("operator", "template_literal"))

            elif node.type == "spread_element":
                operations.add(("operator", "spread"))

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
                elif child.type in ("conditional_expression", "ternary_expression"):
                    complexity += 1
                elif child.type in LOOP_TYPES:
                    complexity += 1
                elif child.type == "catch_clause":
                    complexity += 1
                elif child.type == "switch_case":
                    complexity += 1
                elif child.type == "binary_expression":
                    for c in child.children:
                        if self._node_text(c) in ("&&", "||", "??"):
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

        # Collect defined function names
        defined_funcs = set()
        for node in self._walk():
            if node.type in FUNCTION_TYPES:
                name = self._find_name(node)
                if name != "<anonymous>":
                    defined_funcs.add(name)

        # Build graph
        call_graph = {}
        for node in self._walk():
            if node.type not in FUNCTION_TYPES:
                continue
            name = self._find_name(node)
            if name == "<anonymous>":
                continue

            calls = set()
            for child in self._walk(node):
                if child.type == "call_expression":
                    for c in child.children:
                        if c.type == "identifier":
                            callee = self._node_text(c)
                            if callee in defined_funcs:
                                calls.add(callee)
            call_graph[name] = calls

        return call_graph

    # ── Global Variable Usage ──

    def detect_global_variable_usage(self) -> list:
        """Detect top-level var/let/const referenced inside functions."""
        if not self.tree:
            return []

        # Collect top-level variable names
        module_vars = set()
        root = self.tree.root_node
        for node in root.children:
            if node.type in ("variable_declaration", "lexical_declaration"):
                for child in node.children:
                    if child.type == "variable_declarator":
                        for c in child.children:
                            if c.type == "identifier":
                                module_vars.add(self._node_text(c))
                                break

        if not module_vars:
            return []

        # Find references inside functions
        usage = []
        for node in self._walk():
            if node.type not in FUNCTION_TYPES:
                continue

            name = self._find_name(node)
            referenced = set()
            for child in self._walk(node):
                if child.type == "identifier":
                    ident = self._node_text(child)
                    if ident in module_vars:
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
        """JS has no comprehensions. Return zeros for interface compliance."""
        return {"list": 0, "dict": 0, "set": 0, "generator": 0}

    # ── Executable Lines ──

    def get_executable_lines(self) -> list:
        executable = set()
        if not self.source_code:
            return []

        for i, line in enumerate(self.source_code.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("//"):
                continue
            if stripped.startswith("/*") or stripped.startswith("*"):
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