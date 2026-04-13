"""
Python Parser — ast-based implementation of ParserBase.

Wraps all existing structural feature extraction logic
from Stage1_Semantic.py behind the standardized interface.

Uses Python's built-in ast module (no external deps).
"""

import ast
import sys
from Stage1.Parsers.parser_base import ParserBase


class PythonParser(ParserBase):

    def __init__(self, source_code: str):
        super().__init__(source_code, "python")
        self._docstring_lines = set()

    def parse(self) -> bool:
        try:
            self.tree = ast.parse(self.source_code)
            return True
        except SyntaxError:
            self.tree = None
            return False

    # ── Structural Summary ──

    def extract_structural_summary(self) -> dict:
        if not self.tree:
            return self.empty_summary()

        functions = 0
        classes = 0
        loops = 0
        max_depth = 0
        branches = 0
        self._docstring_lines = set()

        def visit(node, depth=0):
            nonlocal functions, classes, loops, max_depth, branches
            max_depth = max(max_depth, depth)

            if isinstance(node, ast.FunctionDef):
                functions += 1
            if isinstance(node, ast.ClassDef):
                classes += 1
            if isinstance(node, (ast.For, ast.While)):
                loops += 1
            if isinstance(node, (ast.If, ast.IfExp, ast.ExceptHandler)):
                branches += 1

            # Collect docstring lines
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.body:
                    first_stmt = node.body[0]
                    if (isinstance(first_stmt, ast.Expr)
                            and isinstance(first_stmt.value, ast.Constant)
                            and isinstance(first_stmt.value.value, str)):
                        for line_num in range(first_stmt.lineno, first_stmt.end_lineno + 1):
                            self._docstring_lines.add(line_num)

            for child in ast.iter_child_nodes(node):
                visit(child, depth + 1)

        visit(self.tree)

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
        for node in ast.walk(self.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            decorators = []
            is_static = False
            is_classmethod = False
            is_property = False
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name):
                    decorators.append(dec.id)
                    if dec.id == "staticmethod":
                        is_static = True
                    elif dec.id == "classmethod":
                        is_classmethod = True
                    elif dec.id == "property":
                        is_property = True
                elif isinstance(dec, ast.Attribute):
                    decorators.append(ast.unparse(dec))

            params = []
            for arg in node.args.args:
                param = {"name": arg.arg}
                if arg.annotation:
                    try:
                        param["annotation"] = ast.unparse(arg.annotation)
                    except Exception:
                        param["annotation"] = None
                params.append(param)

            defaults = []
            for d in node.args.defaults:
                try:
                    defaults.append(ast.unparse(d))
                except Exception:
                    defaults.append("?")

            return_annotation = None
            if node.returns:
                try:
                    return_annotation = ast.unparse(node.returns)
                except Exception:
                    pass

            parent_class = None
            for cls_node in ast.walk(self.tree):
                if isinstance(cls_node, ast.ClassDef):
                    for item in cls_node.body:
                        if item is node:
                            parent_class = cls_node.name
                            break

            signatures.append({
                "name": node.name,
                "line": node.lineno,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "params": params,
                "defaults": defaults,
                "return_annotation": return_annotation,
                "decorators": decorators,
                "is_static": is_static,
                "is_classmethod": is_classmethod,
                "is_property": is_property,
                "parent_class": parent_class
            })

        return signatures

    # ── Branch Conditions ──

    def extract_branch_conditions(self) -> list:
        if not self.tree:
            return []

        conditions = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.If):
                try:
                    condition_str = ast.unparse(node.test)
                except Exception:
                    condition_str = "?"
                conditions.append({
                    "line": node.lineno,
                    "condition": condition_str,
                    "has_else": len(node.orelse) > 0,
                    "has_elif": (
                        len(node.orelse) == 1
                        and isinstance(node.orelse[0], ast.If)
                    )
                })
        return conditions

    # ── Loop Bounds ──

    def extract_loop_bounds(self) -> list:
        if not self.tree:
            return []

        loops = []
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.For, ast.AsyncFor)):
                try:
                    target = ast.unparse(node.target)
                    iterator = ast.unparse(node.iter)
                except Exception:
                    target = "?"
                    iterator = "?"
                loops.append({
                    "type": "async_for" if isinstance(node, ast.AsyncFor) else "for",
                    "line": node.lineno,
                    "target": target,
                    "iterator": iterator,
                    "condition": None
                })
            elif isinstance(node, ast.While):
                try:
                    condition = ast.unparse(node.test)
                except Exception:
                    condition = "?"
                loops.append({
                    "type": "while",
                    "line": node.lineno,
                    "target": None,
                    "iterator": None,
                    "condition": condition
                })
        return loops

    # ── Return Patterns ──

    def extract_return_patterns(self) -> list:
        if not self.tree:
            return []

        patterns = []
        for node in ast.walk(self.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            returns = []
            for child in ast.walk(node):
                if isinstance(child, ast.Return):
                    try:
                        val = ast.unparse(child.value) if child.value else "None"
                    except Exception:
                        val = "?"
                    returns.append({"line": child.lineno, "value": val})

            has_explicit_return = any(r["value"] != "None" for r in returns)

            patterns.append({
                "function": node.name,
                "line": node.lineno,
                "return_count": len(returns),
                "returns": returns,
                "implicit_none": not has_explicit_return
            })

        return patterns

    # ── Class Hierarchy ──

    def extract_class_hierarchy(self) -> list:
        if not self.tree:
            return []

        classes = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.ClassDef):
                continue

            bases = []
            for base in node.bases:
                try:
                    bases.append(ast.unparse(base))
                except Exception:
                    bases.append("?")

            methods = []
            init_params = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append({
                        "name": item.name,
                        "line": item.lineno,
                        "is_public": not item.name.startswith("_")
                                     or (item.name.startswith("__") and item.name.endswith("__"))
                    })
                    if item.name == "__init__":
                        for arg in item.args.args:
                            if arg.arg != "self":
                                param = {"name": arg.arg}
                                if arg.annotation:
                                    try:
                                        param["annotation"] = ast.unparse(arg.annotation)
                                    except Exception:
                                        pass
                                init_params.append(param)

            classes.append({
                "name": node.name,
                "line": node.lineno,
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
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Try):
                block = {
                    "line": node.lineno,
                    "has_finally": len(node.finalbody) > 0,
                    "has_else": len(node.orelse) > 0,
                    "handlers": []
                }
                for handler in node.handlers:
                    exc_type = None
                    if handler.type:
                        if isinstance(handler.type, ast.Name):
                            exc_type = handler.type.id
                        elif isinstance(handler.type, ast.Tuple):
                            exc_type = [
                                e.id for e in handler.type.elts
                                if isinstance(e, ast.Name)
                            ]
                    block["handlers"].append({
                        "type": exc_type,
                        "line": handler.lineno
                    })
                blocks.append(block)
        return blocks

    # ── Assert Statements ──

    def extract_assert_statements(self) -> list:
        if not self.tree:
            return []

        asserts = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assert):
                try:
                    condition = ast.unparse(node.test)
                except Exception:
                    condition = "?"
                msg = None
                if node.msg:
                    try:
                        msg = ast.unparse(node.msg)
                    except Exception:
                        pass
                asserts.append({
                    "line": node.lineno,
                    "condition": condition,
                    "message": msg
                })
        return asserts

    # ── Import Analysis ──

    def analyze_imports(self) -> list:
        if not self.tree:
            return []

        stdlib_modules = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else set()

        imports = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    imports.append({
                        "module": alias.name,
                        "alias": alias.asname,
                        "names": None,
                        "line": node.lineno,
                        "category": "stdlib" if root in stdlib_modules else "third_party"
                    })
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                names = [a.name for a in node.names] if node.names else []
                imports.append({
                    "module": node.module,
                    "alias": None,
                    "names": names,
                    "line": node.lineno,
                    "category": "stdlib" if root in stdlib_modules else "third_party"
                })
        return imports

    # ── Async Patterns ──

    def detect_async_patterns(self) -> dict:
        if not self.tree:
            return {"async_functions": 0, "await_count": 0, "async_for_count": 0,
                    "async_with_count": 0, "is_async_code": False}

        patterns = {
            "async_functions": 0,
            "await_count": 0,
            "async_for_count": 0,
            "async_with_count": 0,
            "is_async_code": False
        }
        for node in ast.walk(self.tree):
            if isinstance(node, ast.AsyncFunctionDef):
                patterns["async_functions"] += 1
            elif isinstance(node, ast.Await):
                patterns["await_count"] += 1
            elif isinstance(node, ast.AsyncFor):
                patterns["async_for_count"] += 1
            elif isinstance(node, ast.AsyncWith):
                patterns["async_with_count"] += 1

        patterns["is_async_code"] = (
            patterns["async_functions"] > 0 or patterns["await_count"] > 0
        )
        return patterns

    # ── Entry Points ──

    def detect_entry_points(self) -> list:
        if not self.tree:
            return []

        entry_points = []
        for node in ast.iter_child_nodes(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    entry_points.append({
                        "type": "function",
                        "name": node.name,
                        "line": node.lineno,
                        "public_methods": None
                    })
            elif isinstance(node, ast.ClassDef):
                public_methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if (not item.name.startswith("_")
                                or (item.name.startswith("__") and item.name.endswith("__")
                                    and item.name != "__init__")):
                            public_methods.append(item.name)
                if public_methods:
                    entry_points.append({
                        "type": "class",
                        "name": node.name,
                        "line": node.lineno,
                        "public_methods": public_methods
                    })
            elif isinstance(node, ast.If):
                try:
                    cond = ast.unparse(node.test)
                    if "__name__" in cond and "__main__" in cond:
                        entry_points.append({
                            "type": "main_block",
                            "name": "__main__",
                            "line": node.lineno,
                            "public_methods": None
                        })
                except Exception:
                    pass

        return entry_points

    # ── Operation Vocabulary ──

    def extract_operation_vocabulary(self) -> list:
        if not self.tree:
            return []

        operations = set()

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    operations.add(("builtin_or_func", node.func.id))
                elif isinstance(node.func, ast.Attribute):
                    operations.add(("method", node.func.attr))
                    if isinstance(node.func.value, ast.Name):
                        operations.add(("qualified", f"{node.func.value.id}.{node.func.attr}"))
            elif isinstance(node, ast.Subscript):
                if isinstance(node.slice, ast.Slice):
                    operations.add(("operator", "slice"))
                else:
                    operations.add(("operator", "index"))
            elif isinstance(node, ast.BinOp):
                operations.add(("operator", type(node.op).__name__.lower()))
            elif isinstance(node, ast.Compare):
                for op in node.ops:
                    operations.add(("operator", type(op).__name__.lower()))
            elif isinstance(node, ast.BoolOp):
                operations.add(("operator", type(node.op).__name__.lower()))
            elif isinstance(node, ast.UnaryOp):
                operations.add(("operator", type(node.op).__name__.lower()))
            elif isinstance(node, ast.Assert):
                operations.add(("control", "assert"))
            elif isinstance(node, ast.Yield):
                operations.add(("control", "yield"))
            elif isinstance(node, ast.YieldFrom):
                operations.add(("control", "yield_from"))
            elif isinstance(node, ast.Raise):
                exc_type = None
                if node.exc:
                    if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                        exc_type = node.exc.func.id
                    elif isinstance(node.exc, ast.Name):
                        exc_type = node.exc.id
                operations.add(("control", f"raise_{exc_type or 'unknown'}"))
            elif isinstance(node, ast.Await):
                operations.add(("control", "await"))
            elif isinstance(node, ast.Starred):
                operations.add(("operator", "unpack"))
            elif isinstance(node, ast.ListComp):
                operations.add(("control", "listcomp"))
            elif isinstance(node, ast.DictComp):
                operations.add(("control", "dictcomp"))
            elif isinstance(node, ast.SetComp):
                operations.add(("control", "setcomp"))
            elif isinstance(node, ast.GeneratorExp):
                operations.add(("control", "genexp"))

        return [{"category": cat, "name": name} for cat, name in sorted(operations)]

    # ── Cyclomatic Complexity ──

    def compute_cyclomatic_complexity(self) -> list:
        if not self.tree:
            return []

        results = []
        targets = []
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                targets.append(node)

        for func_node in targets:
            complexity = 1
            for node in ast.walk(func_node):
                if isinstance(node, (ast.If, ast.IfExp)):
                    complexity += 1
                elif isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(node, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
                elif isinstance(node, ast.Assert):
                    complexity += 1

            results.append({
                "function": func_node.name,
                "line": func_node.lineno,
                "complexity": complexity
            })

        return results

    # ── Call Graph ──

    def build_call_graph(self) -> dict:
        if not self.tree:
            return {}

        defined_funcs = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                defined_funcs.add(node.name)

        call_graph = {}
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                calls = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                        if child.func.id in defined_funcs:
                            calls.add(child.func.id)
                call_graph[node.name] = calls

        return call_graph

    # ── Global Variable Usage ──

    def detect_global_variable_usage(self) -> list:
        if not self.tree:
            return []

        module_vars = set()
        for node in ast.iter_child_nodes(self.tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        module_vars.add(target.id)
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Name):
                    module_vars.add(node.target.id)

        usage = []
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                declared_global = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Global):
                        declared_global.update(child.names)

                referenced = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and child.id in module_vars:
                        referenced.add(child.id)

                if declared_global or referenced:
                    usage.append({
                        "function": node.name,
                        "line": node.lineno,
                        "declared_global": list(declared_global),
                        "references_module_vars": list(referenced - declared_global)
                    })

        return usage

    # ── Comprehensions ──

    def count_comprehensions(self) -> dict:
        if not self.tree:
            return {"list": 0, "dict": 0, "set": 0, "generator": 0}

        counts = {"list": 0, "dict": 0, "set": 0, "generator": 0}
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ListComp):
                counts["list"] += 1
            elif isinstance(node, ast.DictComp):
                counts["dict"] += 1
            elif isinstance(node, ast.SetComp):
                counts["set"] += 1
            elif isinstance(node, ast.GeneratorExp):
                counts["generator"] += 1
        return counts

    # ── Executable Lines (Python-specific) ──

    def get_executable_lines(self) -> list:
        executable = set()
        if not self.source_code:
            return []

        for i, line in enumerate(self.source_code.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            if i in self._docstring_lines:
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

            for callee in call_graph.get(func, []):
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