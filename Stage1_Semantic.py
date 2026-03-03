"""
Stage1 – Semantic Test and Edge Cases analysis is done here
"""
import ast

class Semantic_Engine:

    def __init__(self, stage0_result: dict, source_code: str):
        assert stage0_result.get("status") == "PASS", \
            "Stage 1 cannot run because Stage 0 did not PASS."

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
        recursion_detected = False

        def visit(current_node, depth=0):
            nonlocal functions, classes, loops, max_depth, recursion_detected

            max_depth = max(max_depth, depth)

            if isinstance(current_node, ast.FunctionDef):
                functions += 1

                for child in ast.walk(current_node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name) and child.func.id == current_node.name:
                            recursion_detected = True

            if isinstance(current_node, ast.ClassDef):
                classes += 1

            if isinstance(current_node, (ast.For, ast.While)):
                loops += 1

            for child in ast.iter_child_nodes(current_node):
                visit(child, depth + 1)

        visit(tree)

        features = {
            "function_count": functions,
            "class_count": classes,
            "loop_count": loops,
            "max_nesting_depth": max_depth,
            "recursion_detected": recursion_detected,

            # Placeholders
            "exception_blocks": None,
            "global_variable_usage": None,
            "comprehension_count": None,
            "branching_factor": None,
            "cyclomatic_complexity": None
        }

        self.context["structural_features"] = features

        return {
            "feature_status": "PARTIAL_SUCCESS",
            "structural_features": features
        }

    def apply_static_risk_heuristics(self):
        features = self.context.get("structural_features")

        if not features:
            return {
                "risk_signals": None,
                "static_risk_score": 0,
                "static_risk_level": "LOW"
            }

        function_count = features.get("function_count", 0)
        loop_count = features.get("loop_count", 0)
        max_depth = features.get("max_nesting_depth", 0)
        recursion = features.get("recursion_detected", False)

        risk_signals = {}
        total_score = 0

        if max_depth > 10:
            severity = "HIGH"
            score = 3
            reason = f"Nesting depth = {max_depth} (>10)"
        elif max_depth > 6:
            severity = "MEDIUM"
            score = 2
            reason = f"Nesting depth = {max_depth} (>6)"
        else:
            severity = "LOW"
            score = 0
            reason = "Nesting depth within safe range"

        if severity != "LOW":
            total_score += score

        risk_signals["complexity_risk"] = {
            "flag": severity != "LOW",
            "severity": severity,
            "reason": reason
        }

        if recursion:
            severity = "HIGH"
            score = 3
            reason = "Direct recursion detected"
            total_score += score
        else:
            severity = "LOW"
            score = 0
            reason = "No recursion detected"

        risk_signals["recursion_risk"] = {
            "flag": recursion,
            "severity": severity,
            "reason": reason
        }

        if loop_count >= 3:
            severity = "HIGH"
            score = 3
            reason = f"{loop_count} loops detected (>=3)"
        elif loop_count >= 2:
            severity = "MEDIUM"
            score = 2
            reason = f"{loop_count} loops detected (>=2)"
        else:
            severity = "LOW"
            score = 0
            reason = "Loop count within safe range"

        if severity != "LOW":
            total_score += score

        risk_signals["performance_risk"] = {
            "flag": severity != "LOW",
            "severity": severity,
            "reason": reason
        }

        if function_count >= 5:
            severity = "MEDIUM"
            score = 1
            reason = f"{function_count} functions detected (>=5)"
            total_score += score
        else:
            severity = "LOW"
            score = 0
            reason = "Function count within normal range"

        risk_signals["structural_instability_risk"] = {
            "flag": severity != "LOW",
            "severity": severity,
            "reason": reason
        }

        if total_score >= 7:
            risk_level = "HIGH"
        elif total_score >= 3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "risk_signals": risk_signals,
            "static_risk_score": total_score,
            "static_risk_level": risk_level
        }

    def run(self):
        init_output = self.initialize()
        ast_output = self.parse_ast()
        feature_output = self.extract_structural_features()
        risk_output = self.apply_static_risk_heuristics()

        return {
            "stage": 1,
            "status": "STAGE1_COMPLETE",
            "language": self.language,
            **init_output,
            **ast_output,
            **feature_output,
            **risk_output
        }