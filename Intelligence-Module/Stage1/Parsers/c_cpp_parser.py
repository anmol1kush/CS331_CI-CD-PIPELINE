"""
C/C++ Parser — tree-sitter based implementation of ParserBase.

Uses tree-sitter-c grammar. C++ shares most node types
with C at the structural level we care about (functions, loops, branches).
For the current increment, both C and C++ use the C grammar
which covers the common structural patterns.

Future: use tree-sitter-cpp for C++-specific features
(templates, namespaces, RAII patterns).
"""

import tree_sitter_c as ts_c
from tree_sitter import Language, Parser
from Stage1.Parsers.parser_base import ParserBase


FUNCTION_TYPES = {"function_definition"}
LOOP_TYPES = {"for_statement", "while_statement", "do_statement"}
BRANCH_TYPES = {"if_statement", "case_statement", "conditional_expression"}


class CCppParser(ParserBase):

    def __init__(self, source_code: str, language: str = "c"):
        super().__init__(source_code, language)
        self._parser = Parser()
        lang = Language(ts_c.language())
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
        """Find the function name from a function_definition node."""
        for child in node.children:
            if child.type == "function_declarator":
                for c in child.children:
                    if c.type == "identifier":
                        return self._node_text(c)
            if child.type == "identifier":
                return self._node_text(child)
        return "<unknown>"

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
            if node.type == "struct_specifier":
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

            # Return type
            return_type = None
            for child in node.children:
                if child.type in ("primitive_type", "type_identifier", "sized_type_specifier"):
                    return_type = self._node_text(child)
                    break

            # Parameters
            params = []
            for child in node.children:
                if child.type == "function_declarator":
                    for c in child.children:
                        if c.type == "parameter_list":
                            for p in c.children:
                                if p.type == "parameter_declaration":
                                    p_name = ""
                                    p_type = ""
                                    for pp in p.children:
                                        if pp.type == "identifier":
                                            p_name = self._node_text(pp)
                                        elif pp.type in ("primitive_type", "type_identifier",
                                                         "sized_type_specifier"):
                                            p_type = self._node_text(pp)
                                    params.append({
                                        "name": p_name,
                                        "annotation": p_type if p_type else None
                                    })

            # Check if static
            is_static = False
            for child in node.children:
                if child.type == "storage_class_specifier" and self._node_text(child) == "static":
                    is_static = True

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
                "parent_class": None
            })

        return signatures

    # ── Branch Conditions ──

    def extract_branch_conditions(self) -> list:
        if not self.tree:
            return []

        conditions = []
        for node in self._walk():
            if node.type == "if_statement":
                cond_node = None
                has_else = False
                has_elif = False

                for child in node.children:
                    if child.type == "parenthesized_expression":
                        cond_node = child
                    if child.type == "else_clause":
                        has_else = True
                        for gc in child.children:
                            if gc.type == "if_statement":
                                has_elif = True

                conditions.append({
                    "line": node.start_point[0] + 1,
                    "condition": self._node_text(cond_node) if cond_node else "?",
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
                    val_parts = [c for c in child.children if c.type not in ("return", ";")]
                    val = self._node_text(val_parts[0]) if val_parts else "void"
                    returns.append({
                        "line": child.start_point[0] + 1,
                        "value": val
                    })

            # Check if void return type
            is_void = False
            for child in node.children:
                if child.type == "primitive_type" and self._node_text(child) == "void":
                    is_void = True

            patterns.append({
                "function": name,
                "line": node.start_point[0] + 1,
                "return_count": len(returns),
                "returns": returns,
                "implicit_none": is_void
            })

        return patterns

    # ── Class Hierarchy (structs in C) ──

    def extract_class_hierarchy(self) -> list:
        if not self.tree:
            return []

        classes = []
        for node in self._walk():
            if node.type == "struct_specifier":
                name = self._find_name(node)
                classes.append({
                    "name": name,
                    "line": node.start_point[0] + 1,
                    "bases": [],
                    "methods": [],
                    "init_params": []
                })

        return classes

    # ── Exception Blocks ──

    def extract_exception_blocks(self) -> list:
        """C has no exception handling. Return empty."""
        return []

    # ── Assert Statements ──

    def extract_assert_statements(self) -> list:
        """Look for assert() macro calls."""
        if not self.tree:
            return []

        asserts = []
        for node in self._walk():
            if node.type == "call_expression":
                func_name = ""
                for child in node.children:
                    if child.type == "identifier":
                        func_name = self._node_text(child)
                if func_name == "assert":
                    args = []
                    for child in node.children:
                        if child.type == "argument_list":
                            args = [self._node_text(a) for a in child.children
                                    if a.type not in ("(", ")", ",")]
                    asserts.append({
                        "line": node.start_point[0] + 1,
                        "condition": args[0] if args else "?",
                        "message": None
                    })

        return asserts

    # ── Import Analysis ──

    def analyze_imports(self) -> list:
        if not self.tree:
            return []

        c_stdlib = {"stdio", "stdlib", "string", "math", "time", "ctype",
                    "errno", "signal", "assert", "limits", "float", "stddef",
                    "stdarg", "setjmp", "locale", "stdbool", "stdint", "inttypes",
                    "complex", "iso646", "wchar", "wctype", "fenv", "tgmath"}

        imports = []
        for node in self._walk():
            if node.type == "preproc_include":
                path_node = None
                for child in node.children:
                    if child.type in ("system_lib_string", "string_literal"):
                        path_node = child

                if path_node:
                    module = self._node_text(path_node).strip("<>\"/")
                    root = module.replace(".h", "").split("/")[0]
                    is_system = path_node.type == "system_lib_string"
                    imports.append({
                        "module": module,
                        "alias": None,
                        "names": None,
                        "line": node.start_point[0] + 1,
                        "category": "stdlib" if root in c_stdlib or is_system else "third_party"
                    })

        return imports

    # ── Async Patterns ──

    def detect_async_patterns(self) -> dict:
        """C has no native async. Return zeros."""
        return {
            "async_functions": 0, "await_count": 0,
            "async_for_count": 0, "async_with_count": 0,
            "is_async_code": False
        }

    # ── Entry Points ──

    def detect_entry_points(self) -> list:
        if not self.tree:
            return []

        entry_points = []
        for node in self._walk():
            if node.type in FUNCTION_TYPES:
                name = self._find_name(node)
                if name == "main":
                    entry_points.append({
                        "type": "main_block",
                        "name": "main",
                        "line": node.start_point[0] + 1,
                        "public_methods": None
                    })
                elif not name.startswith("_"):
                    entry_points.append({
                        "type": "function",
                        "name": name,
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
            elif node.type == "binary_expression":
                for child in node.children:
                    text = self._node_text(child)
                    if text in ("+", "-", "*", "/", "%", "==", "!=", "<", ">",
                                "<=", ">=", "&&", "||", "&", "|", "^", "<<", ">>"):
                        operations.add(("operator", text))
            elif node.type == "unary_expression":
                for child in node.children:
                    text = self._node_text(child)
                    if text in ("!", "-", "+", "~", "*", "&", "++", "--"):
                        operations.add(("operator", text))
            elif node.type == "subscript_expression":
                operations.add(("operator", "index"))
            elif node.type == "pointer_expression":
                operations.add(("operator", "pointer_deref"))
            elif node.type == "sizeof_expression":
                operations.add(("builtin_or_func", "sizeof"))

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
                elif child.type == "case_statement":
                    complexity += 1
                elif child.type == "conditional_expression":
                    complexity += 1
                elif child.type == "binary_expression":
                    for c in child.children:
                        if self._node_text(c) in ("&&", "||"):
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

        defined_funcs = set()
        for node in self._walk():
            if node.type in FUNCTION_TYPES:
                defined_funcs.add(self._find_name(node))

        call_graph = {}
        for node in self._walk():
            if node.type not in FUNCTION_TYPES:
                continue
            name = self._find_name(node)
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
        if not self.tree:
            return []

        # Collect top-level declarations
        global_vars = set()
        root = self.tree.root_node
        for node in root.children:
            if node.type == "declaration":
                for child in node.children:
                    if child.type == "init_declarator":
                        for c in child.children:
                            if c.type == "identifier":
                                global_vars.add(self._node_text(c))
                    elif child.type == "identifier":
                        global_vars.add(self._node_text(child))

        if not global_vars:
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
                    if ident in global_vars:
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
        """C has no comprehensions."""
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
            if "/*" in stripped:
                in_block_comment = True
            if in_block_comment:
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("//"):
                continue
            if stripped.startswith("#"):  # preprocessor directives
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