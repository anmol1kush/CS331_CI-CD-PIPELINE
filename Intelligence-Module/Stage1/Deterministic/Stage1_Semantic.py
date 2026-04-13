"""
Stage1 – Semantic Analysis Engine

Orchestrates structural feature extraction by delegating
to language-specific parsers via the Parser Factory.

Responsibilities:
    - Validate Stage 0 passed
    - Normalize source code
    - Detect execution model (language-aware)
    - Delegate all AST parsing and feature extraction to Parsers/
    - Assemble and return the unified output dict

This file contains NO ast.* calls. All parsing is done
by Stage1/Parsers/ implementations.
"""

from Stage1.Parsers.parser_factory import get_parser


class Semantic_Engine:

    def __init__(self, stage0_result: dict, source_code: str):
        if stage0_result.get("status") != "PASS":
            raise ValueError("Stage 1 cannot run because Stage 0 did not PASS.")

        self.stage0_result = stage0_result
        self.source_code = source_code
        self.language = stage0_result.get("language")
        self.parser = None

        self.context = {
            "stage": 1,
            "language": self.language,
            "metadata": {},
            "normalized_code": None,
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

        model = self.detect_execution_model(code)
        self.context["metadata"]["execution_model"] = model

        return {"execution_model": model}

    def detect_execution_model(self, code: str) -> str:
        """Language-aware execution model detection."""
        if not code:
            return "unknown"

        if self.language == "python":
            if "class Solution" in code:
                return "callable_method"
            elif "input(" in code:
                return "stdin_program"
            else:
                return "script"

        elif self.language in ("javascript", "typescript"):
            if ("module.exports" in code or
                    "export default" in code or
                    "export function" in code or
                    "export class" in code):
                return "callable_method"
            elif "process.stdin" in code or "readline" in code:
                return "stdin_program"
            else:
                return "script"

        elif self.language == "java":
            if "public static void main" in code:
                return "stdin_program"
            else:
                return "callable_method"

        elif self.language in ("c", "cpp"):
            if "int main" in code or "void main" in code:
                return "stdin_program"
            else:
                return "callable_method"

        return "unknown"

    def parse_ast(self):
        """Initialize parser and parse source code."""
        code = self.context["normalized_code"]

        try:
            self.parser = get_parser(self.language, code)
            success = self.parser.parse()

            if success:
                self.context["metadata"]["ast_status"] = "SUCCESS"
                return {"ast_status": "SUCCESS"}
            else:
                self.context["metadata"]["ast_status"] = "FAILED"
                return {"ast_status": "FAILED"}

        except ValueError as e:
            # Unsupported language
            self.context["metadata"]["ast_status"] = "UNSUPPORTED"
            return {"ast_status": "UNSUPPORTED", "ast_error": str(e)}

        except Exception as e:
            self.context["metadata"]["ast_status"] = "FAILED"
            return {"ast_status": "FAILED", "ast_error": str(e)}

    def extract_structural_features(self):
        """Delegate all feature extraction to the parser."""
        if not self.parser or self.context["metadata"].get("ast_status") != "SUCCESS":
            return {
                "feature_status": "SKIPPED",
                "structural_features": None
            }

        summary = self.parser.extract_structural_summary()

        features = {
            # From structural summary
            "function_count": summary["function_count"],
            "class_count": summary["class_count"],
            "loop_count": summary["loop_count"],
            "max_nesting_depth": summary["max_nesting_depth"],
            "recursiondetected": summary["recursiondetected"],
            "direct_recursion": summary["direct_recursion"],
            "mutual_recursion": summary["mutual_recursion"],
            "recursion_cycles": summary["recursion_cycles"],
            "line_count": summary["line_count"],
            "branching_factor": summary["branching_factor"],
            "executable_lines": summary["executable_lines"],

            # Individual feature extractions
            "exception_blocks": self.parser.extract_exception_blocks(),
            "global_variable_usage": self.parser.detect_global_variable_usage(),
            "comprehension_count": self.parser.count_comprehensions(),
            "cyclomatic_complexity": self.parser.compute_cyclomatic_complexity(),
            "method_signatures": self.parser.extract_method_signatures(),
            "branch_conditions": self.parser.extract_branch_conditions(),
            "loop_bounds": self.parser.extract_loop_bounds(),
            "return_patterns": self.parser.extract_return_patterns(),
            "class_hierarchy": self.parser.extract_class_hierarchy(),
            "assert_statements": self.parser.extract_assert_statements(),
            "import_analysis": self.parser.analyze_imports(),
            "async_patterns": self.parser.detect_async_patterns(),
            "entry_points": self.parser.detect_entry_points(),
            "operation_vocabulary": self.parser.extract_operation_vocabulary()
        }

        self.context["structural_features"] = features

        return {
            "feature_status": "SUCCESS",
            "structural_features": features
        }

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