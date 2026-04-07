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

            # Placeholders
            "exception_blocks": None,
            "global_variable_usage": None,
            "comprehension_count": None,
            "cyclomatic_complexity": None
        }

        self.context["structural_features"] = features

        return {
            "feature_status": "PARTIAL_SUCCESS",
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