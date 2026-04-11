"""
Stage1 – Semantic Tests and Edge Cases analysis is done here
"""
import ast

class Semantic_Engine:

    def __init__(self, stage0_result: dict, source_code: str):
        # assert stage0_result.get("status") == "PASS", \
        #     "Stage 1 cannot run because Stage 0 did not PASS."
        if stage0_result.get("status") != "PASS":
            raise ValueError("Stage 1 cannot run because Stage 0 did not PASS.")

        self.stage0_result = stage0_result
        self.source_code = source_code
        self.language = stage0_result.get("language")

        self.context = {
            "stage": 1,
            "language": self.language,
            "metadata": {},
            "normalized_code": None,
            "ast_tree": None,
            "structural_features": None
        }

    def initialize(self):
        if not isinstance(self.source_code, str):
            self.context["normalized_code"] = ""
        else:
            code = self.source_code.replace("\r\n", "\n").strip()
            self.context["normalized_code"] = code

        code = self.context["normalized_code"]

        self.context["metadata"]["line_count"] = len(code.splitlines()) if code else 0

        if self.language == "python":
            if "class Solution" in code:
                model = "callable_method"
            elif "input(" in code:
                model = "stdin_program"
            else:
                model = "script"
        elif self.language in ["c", "cpp"]:
            model = "stdin_program" if "main(" in code else "unknown"
        elif self.language == "java":
            model = "stdin_program" if "public static void main" in code else "callable_method"
        else:
            model = "unknown"

        self.context["metadata"]["execution_model"] = model

        return {
            "execution_model": model
        }

    def parse_ast(self):

        if self.language != "python":
            self.context["metadata"]["ast_status"] = "EXTERNAL_REQUIRED"
            return {
                "ast_status": "EXTERNAL_REQUIRED"
            }

        try:
            tree = ast.parse(self.context["normalized_code"])
            self.context["ast_tree"] = tree
            self.context["metadata"]["ast_status"] = "SUCCESS"

            return {
                "ast_status": "SUCCESS"
            }

        except SyntaxError as e:
            self.context["ast_tree"] = None
            self.context["metadata"]["ast_status"] = "FAILED"

            return {
                "ast_status": "FAILED",
                "ast_error": str(e)
            }

    def build_call_graph(self, tree):
        defined_funcs = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined_funcs.add(node.name)

        call_graph = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                calls = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                        if child.func.id in defined_funcs:
                            calls.add(child.func.id)
                call_graph[node.name] = calls

        return call_graph

    def detect_recursion(self, call_graph):
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

    def count_exception_blocks(self, tree):
        """Extract try/except/finally structures with exception types."""
        blocks = []
        for node in ast.walk(tree):
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

    def detect_global_variable_usage(self, tree):
        """Detect module-level variables referenced/modified inside functions."""
        # Collect module-level assignments
        module_vars = set()
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        module_vars.add(target.id)
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Name):
                    module_vars.add(node.target.id)

        # Find references inside functions
        usage = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for explicit global declarations
                declared_global = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Global):
                        declared_global.update(child.names)

                # Check for module-level var references
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

    def count_comprehensions(self, tree):
        """Count list/dict/set/generator comprehensions."""
        counts = {"list": 0, "dict": 0, "set": 0, "generator": 0}
        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                counts["list"] += 1
            elif isinstance(node, ast.DictComp):
                counts["dict"] += 1
            elif isinstance(node, ast.SetComp):
                counts["set"] += 1
            elif isinstance(node, ast.GeneratorExp):
                counts["generator"] += 1
        return counts

    def compute_cyclomatic_complexity(self, tree):
        """Compute per-function McCabe cyclomatic complexity."""
        results = []
        targets = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                targets.append(node)

        for func_node in targets:
            complexity = 1  # base path
            for node in ast.walk(func_node):
                if isinstance(node, (ast.If, ast.IfExp)):
                    complexity += 1
                elif isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(node, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    # each and/or adds a decision point
                    complexity += len(node.values) - 1
                elif isinstance(node, ast.Assert):
                    complexity += 1

            results.append({
                "function": func_node.name,
                "line": func_node.lineno,
                "complexity": complexity
            })

        return results

    def extract_method_signatures(self, tree):
        """Extract all function/method signatures with params, decorators, annotations."""
        signatures = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Determine method kind
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

                # Extract parameters
                params = []
                for arg in node.args.args:
                    param = {"name": arg.arg}
                    if arg.annotation:
                        try:
                            param["annotation"] = ast.unparse(arg.annotation)
                        except Exception:
                            param["annotation"] = None
                    params.append(param)

                # Defaults
                defaults = []
                for d in node.args.defaults:
                    try:
                        defaults.append(ast.unparse(d))
                    except Exception:
                        defaults.append("?")

                # Return annotation
                return_annotation = None
                if node.returns:
                    try:
                        return_annotation = ast.unparse(node.returns)
                    except Exception:
                        pass

                # Find parent class if any
                parent_class = None
                for cls_node in ast.walk(tree):
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

    def extract_branch_conditions(self, tree):
        """Extract actual condition expressions from if/elif with line numbers."""
        conditions = []
        for node in ast.walk(tree):
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

    def extract_loop_bounds(self, tree):
        """Extract loop target/iterator expressions with line numbers."""
        loops = []
        for node in ast.walk(tree):
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
                    "iterator": iterator
                })
            elif isinstance(node, ast.While):
                try:
                    condition = ast.unparse(node.test)
                except Exception:
                    condition = "?"
                loops.append({
                    "type": "while",
                    "line": node.lineno,
                    "condition": condition
                })
        return loops

    def extract_return_patterns(self, tree):
        """Per function: return points, expressions, implicit None returns."""
        patterns = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                returns = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        try:
                            val = ast.unparse(child.value) if child.value else "None"
                        except Exception:
                            val = "?"
                        returns.append({
                            "line": child.lineno,
                            "value": val
                        })

                # Detect implicit None return (no return or return without value)
                has_explicit_return = any(
                    r["value"] != "None" for r in returns
                )

                patterns.append({
                    "function": node.name,
                    "line": node.lineno,
                    "return_count": len(returns),
                    "returns": returns,
                    "implicit_none": not has_explicit_return
                })

        return patterns

    def extract_class_hierarchy(self, tree):
        """Class names, bases, method list, __init__ params."""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
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
                                         or item.name.startswith("__") and item.name.endswith("__")
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

    def extract_assert_statements(self, tree):
        """Extract assert conditions as implicit specs/constraints."""
        asserts = []
        for node in ast.walk(tree):
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

    def analyze_imports(self, tree):
        """Categorize imports as stdlib vs third-party."""
        import sys
        stdlib_modules = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else set()

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    imports.append({
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                        "category": "stdlib" if root in stdlib_modules else "third_party"
                    })
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                names = [a.name for a in node.names] if node.names else []
                imports.append({
                    "module": node.module,
                    "names": names,
                    "line": node.lineno,
                    "category": "stdlib" if root in stdlib_modules else "third_party"
                })
        return imports

    def detect_async_patterns(self, tree):
        """Detect async def, await, async for, async with."""
        patterns = {
            "async_functions": 0,
            "await_count": 0,
            "async_for_count": 0,
            "async_with_count": 0,
            "is_async_code": False
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                patterns["async_functions"] += 1
            elif isinstance(node, ast.Await):
                patterns["await_count"] += 1
            elif isinstance(node, ast.AsyncFor):
                patterns["async_for_count"] += 1
            elif isinstance(node, ast.AsyncWith):
                patterns["async_with_count"] += 1

        patterns["is_async_code"] = (
                patterns["async_functions"] > 0 or
                patterns["await_count"] > 0
        )
        return patterns

    def detect_entry_points(self, tree):
        """Generalized entry point detection for any Python file."""
        entry_points = []

        for node in ast.iter_child_nodes(tree):
            # Public standalone functions (not inside classes)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    entry_points.append({
                        "type": "function",
                        "name": node.name,
                        "line": node.lineno
                    })

            # Classes with public methods
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

            # if __name__ == "__main__" block
            elif isinstance(node, ast.If):
                try:
                    cond = ast.unparse(node.test)
                    if "__name__" in cond and "__main__" in cond:
                        entry_points.append({
                            "type": "main_block",
                            "name": "__main__",
                            "line": node.lineno
                        })
                except Exception:
                    pass

        return entry_points

    def extract_operation_vocabulary(self, tree):
        """
        Extract all callable operations present in the source code.
        This is the reference vocabulary for dynamic test signatures.

        Captures:
        - Built-in function calls (len, sorted, print, range, etc.)
        - Method calls on objects (.append, .pop, .sort, etc.)
        - Standard library calls (heapq.heappush, math.log, etc.)
        - User-defined function calls
        - Operators that map to dunder methods ([], +, *, in, etc.)
        - Assert statements
        - Yield / yield from (generator behavior)
        - Raise statements (exception throwing)
        """
        operations = set()

        for node in ast.walk(tree):
            # Direct function calls: len(), sorted(), print()
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    operations.add(("builtin_or_func", node.func.id))
                # Method calls: obj.append(), heapq.heappush()
                elif isinstance(node.func, ast.Attribute):
                    operations.add(("method", node.func.attr))
                    # Also capture module.method pattern
                    if isinstance(node.func.value, ast.Name):
                        operations.add(("qualified", f"{node.func.value.id}.{node.func.attr}"))

            # Subscript operations: obj[key], obj[i:j]
            elif isinstance(node, ast.Subscript):
                if isinstance(node.slice, ast.Slice):
                    operations.add(("operator", "slice"))
                else:
                    operations.add(("operator", "index"))

            # Binary operators: +, -, *, /, //, %, **
            elif isinstance(node, ast.BinOp):
                op_name = type(node.op).__name__.lower()
                operations.add(("operator", op_name))

            # Comparison operators: ==, !=, <, >, <=, >=, in, not in, is
            elif isinstance(node, ast.Compare):
                for op in node.ops:
                    op_name = type(op).__name__.lower()
                    operations.add(("operator", op_name))

            # Boolean operators: and, or
            elif isinstance(node, ast.BoolOp):
                op_name = type(node.op).__name__.lower()
                operations.add(("operator", op_name))

            # Unary operators: not, -, +, ~
            elif isinstance(node, ast.UnaryOp):
                op_name = type(node.op).__name__.lower()
                operations.add(("operator", op_name))

            # Assert statements
            elif isinstance(node, ast.Assert):
                operations.add(("control", "assert"))

            # Yield / yield from (generator behavior)
            elif isinstance(node, ast.Yield):
                operations.add(("control", "yield"))
            elif isinstance(node, ast.YieldFrom):
                operations.add(("control", "yield_from"))

            # Raise statements
            elif isinstance(node, ast.Raise):
                exc_type = None
                if node.exc:
                    if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                        exc_type = node.exc.func.id
                    elif isinstance(node.exc, ast.Name):
                        exc_type = node.exc.id
                operations.add(("control", f"raise_{exc_type or 'unknown'}"))

            # Await expressions
            elif isinstance(node, ast.Await):
                operations.add(("control", "await"))

            # Starred expressions (unpacking)
            elif isinstance(node, ast.Starred):
                operations.add(("operator", "unpack"))

            # Comprehensions (as operations, not just count)
            elif isinstance(node, ast.ListComp):
                operations.add(("control", "listcomp"))
            elif isinstance(node, ast.DictComp):
                operations.add(("control", "dictcomp"))
            elif isinstance(node, ast.SetComp):
                operations.add(("control", "setcomp"))
            elif isinstance(node, ast.GeneratorExp):
                operations.add(("control", "genexp"))

        # Convert to serializable list of dicts
        vocab = []
        for category, name in sorted(operations):
            vocab.append({"category": category, "name": name})

        return vocab

    def extract_structural_features(self):
        tree = self.context.get("ast_tree")

        if not tree:
            return {
                "feature_status": "SKIPPED",
                "structural_features": None
            }

        functions = 0
        classes = 0
        loops = 0
        max_depth = 0
        branches = 0
        recursion_detected = False
        docstring_lines = set()

        def visit(current_node, depth=0):
            nonlocal functions, classes, loops, max_depth,branches, recursion_detected

            max_depth = max(max_depth, depth)

            if isinstance(current_node, ast.FunctionDef):
                functions += 1

            if isinstance(current_node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if current_node.body:
                    first_stmt = current_node.body[0]
                    if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value,
                                                                       ast.Constant) and isinstance(
                            first_stmt.value.value, str):
                        for line_num in range(first_stmt.lineno, first_stmt.end_lineno + 1):
                            docstring_lines.add(line_num)
                # for child in ast.walk(current_node):
                #     if isinstance(child, ast.Call):
                #         if isinstance(child.func, ast.Name) and child.func.id == current_node.name:
                #             recursion_detected = True

            if isinstance(current_node, ast.ClassDef):
                classes += 1

            if isinstance(current_node, (ast.For, ast.While)):
                loops += 1

            if isinstance(current_node, (ast.If, ast.IfExp, ast.ExceptHandler)):
                branches += 1

            for child in ast.iter_child_nodes(current_node):
                visit(child, depth + 1)

        visit(tree)

        code = self.context.get("normalized_code", "")
        executable = set()
        if code:
            for i, line in enumerate(code.splitlines(), start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    continue
                if i in docstring_lines:
                    continue
                executable.add(i)


        call_graph = self.build_call_graph(tree)
        recursion_info = self.detect_recursion(call_graph)

        features = {
            "function_count": functions,
            "class_count": classes,
            "loop_count": loops,
            "max_nesting_depth": max_depth,
            "recursion_detected": recursion_detected,
            "direct_recursion": recursion_info["direct_recursion"],
            "mutual_recursion": recursion_info["mutual_recursion"],
            "recursion_cycles": recursion_info["cycles"],
            "line_count": self.context["metadata"].get("line_count", 0),
            "branching_factor": branches,
            "executable_lines": list(executable),
            "exception_blocks": self.count_exception_blocks(tree),
            "global_variable_usage": self.detect_global_variable_usage(tree),
            "comprehension_count": self.count_comprehensions(tree),
            "cyclomatic_complexity": self.compute_cyclomatic_complexity(tree),
            "method_signatures": self.extract_method_signatures(tree),
            "branch_conditions": self.extract_branch_conditions(tree),
            "loop_bounds": self.extract_loop_bounds(tree),
            "return_patterns": self.extract_return_patterns(tree),
            "class_hierarchy": self.extract_class_hierarchy(tree),
            "assert_statements": self.extract_assert_statements(tree),
            "import_analysis": self.analyze_imports(tree),
            "async_patterns": self.detect_async_patterns(tree),
            "entry_points": self.detect_entry_points(tree),
            "operation_vocabulary": self.extract_operation_vocabulary(tree)
        }

        self.context["structural_features"] = features

        return {
            "feature_status": "SUCCESS",
            "structural_features": features
        }

    # def apply_static_risk_heuristics(self):
    #     features = self.context.get("structural_features")
    #
    #     if not features:
    #         return {
    #             "risk_signals": None,
    #             "static_risk_score": 0,
    #             "static_risk_level": "LOW"
    #         }
    #
    #     function_count = features.get("function_count", 0)
    #     loop_count = features.get("loop_count", 0)
    #     max_depth = features.get("max_nesting_depth", 0)
    #     recursion = features.get("recursion_detected", False)
    #
    #     risk_signals = {}
    #     total_score = 0
    #
    #     if max_depth > 10:
    #         severity = "HIGH"
    #         score = 3
    #         reason = f"Nesting depth = {max_depth} (>10)"
    #     elif max_depth > 6:
    #         severity = "MEDIUM"
    #         score = 2
    #         reason = f"Nesting depth = {max_depth} (>6)"
    #     else:
    #         severity = "LOW"
    #         score = 0
    #         reason = "Nesting depth within safe range"
    #
    #     if severity != "LOW":
    #         total_score += score
    #
    #     risk_signals["complexity_risk"] = {
    #         "flag": severity != "LOW",
    #         "severity": severity,
    #         "reason": reason
    #     }
    #
    #     if recursion:
    #         severity = "HIGH"
    #         score = 3
    #         reason = "Direct recursion detected"
    #         total_score += score
    #     else:
    #         severity = "LOW"
    #         score = 0
    #         reason = "No recursion detected"
    #
    #     risk_signals["recursion_risk"] = {
    #         "flag": recursion,
    #         "severity": severity,
    #         "reason": reason
    #     }
    #
    #     if loop_count >= 3:
    #         severity = "HIGH"
    #         score = 3
    #         reason = f"{loop_count} loops detected (>=3)"
    #     elif loop_count >= 2:
    #         severity = "MEDIUM"
    #         score = 2
    #         reason = f"{loop_count} loops detected (>=2)"
    #     else:
    #         severity = "LOW"
    #         score = 0
    #         reason = "Loop count within safe range"
    #
    #     if severity != "LOW":
    #         total_score += score
    #
    #     risk_signals["performance_risk"] = {
    #         "flag": severity != "LOW",
    #         "severity": severity,
    #         "reason": reason
    #     }
    #
    #     if function_count >= 5:
    #         severity = "MEDIUM"
    #         score = 1
    #         reason = f"{function_count} functions detected (>=5)"
    #         total_score += score
    #     else:
    #         severity = "LOW"
    #         score = 0
    #         reason = "Function count within normal range"
    #
    #     risk_signals["structural_instability_risk"] = {
    #         "flag": severity != "LOW",
    #         "severity": severity,
    #         "reason": reason
    #     }
    #
    #     if total_score >= 7:
    #         risk_level = "HIGH"
    #     elif total_score >= 3:
    #         risk_level = "MEDIUM"
    #     else:
    #         risk_level = "LOW"
    #
    #     return {
    #         "risk_signals": risk_signals,
    #         "static_risk_score": total_score,
    #         "static_risk_level": risk_level
    #     }

    def run(self):
        init_output = self.initialize()
        ast_output = self.parse_ast()
        feature_output = self.extract_structural_features()

        features = feature_output.get("structural_features") or {}
        executable_lines = features.get("executable_lines", [])

        return {
            "stage": 1,
            "status": "STAGE1_COMPLETE",
            "language": self.language,
            "normalized_code": self.context["normalized_code"],
            "executable_lines": executable_lines,
            **init_output,
            **ast_output,
            **feature_output
        }