"""
Parser Base — Abstract interface for language-specific AST parsers.

Every parser implementation must produce the SAME output shapes
regardless of language. This is the SoC boundary between
Stage1_Semantic.py and language-specific AST libraries.

Downstream consumers (State, Objective, LLM prompts, coverage_analyzer)
depend ONLY on the dict shapes defined here, never on ast/tree-sitter directly.

Current implementations:
    - PythonParser (ast module)
    - JSTSParser (tree-sitter-javascript / tree-sitter-typescript)
    - JavaParser (tree-sitter-java)
    - CCppParser (tree-sitter-c / tree-sitter-cpp)
"""

from abc import ABC, abstractmethod


class ParserBase(ABC):
    """
    Abstract base class for all language parsers.

    Each method returns a standardized dict/list shape.
    Implementations fill these shapes using their native AST library.
    """

    def __init__(self, source_code: str, language: str):
        self.source_code = source_code
        self.language = language
        self.tree = None

    @abstractmethod
    def parse(self) -> bool:
        """
        Parse source_code into internal tree representation.
        Returns True if parsing succeeded, False otherwise.
        Sets self.tree internally.
        """
        pass

    @abstractmethod
    def extract_structural_summary(self) -> dict:
        """
        Top-level counts and flags.

        Returns:
            {
                "function_count": int,
                "class_count": int,
                "loop_count": int,
                "max_nesting_depth": int,
                "branching_factor": int,
                "line_count": int,
                "executable_lines": list[int],
                "recursion_detected": bool,
                "direct_recursion": bool,
                "mutual_recursion": bool,
                "recursion_cycles": list
            }
        """
        pass

    @abstractmethod
    def extract_method_signatures(self) -> list:
        """
        Returns:
            [
                {
                    "name": str,
                    "line": int,
                    "is_async": bool,
                    "params": [{"name": str, "annotation": str|None}],
                    "defaults": list,
                    "return_annotation": str|None,
                    "decorators": list,
                    "is_static": bool,
                    "is_classmethod": bool,
                    "is_property": bool,
                    "parent_class": str|None
                }
            ]
        """
        pass

    @abstractmethod
    def extract_branch_conditions(self) -> list:
        """
        Returns:
            [
                {
                    "line": int,
                    "condition": str,
                    "has_else": bool,
                    "has_elif": bool
                }
            ]
        """
        pass

    @abstractmethod
    def extract_loop_bounds(self) -> list:
        """
        Returns:
            [
                {
                    "type": str,       # "for" | "while" | "async_for" | "for_in" | "for_of"
                    "line": int,
                    "target": str|None,
                    "iterator": str|None,
                    "condition": str|None
                }
            ]
        """
        pass

    @abstractmethod
    def extract_return_patterns(self) -> list:
        """
        Returns:
            [
                {
                    "function": str,
                    "line": int,
                    "return_count": int,
                    "returns": [{"line": int, "value": str}],
                    "implicit_none": bool
                }
            ]
        """
        pass

    @abstractmethod
    def extract_class_hierarchy(self) -> list:
        """
        Returns:
            [
                {
                    "name": str,
                    "line": int,
                    "bases": list[str],
                    "methods": [{"name": str, "line": int, "is_public": bool}],
                    "init_params": [{"name": str, "annotation": str|None}]
                }
            ]
        """
        pass

    @abstractmethod
    def extract_exception_blocks(self) -> list:
        """
        Returns:
            [
                {
                    "line": int,
                    "has_finally": bool,
                    "has_else": bool,          # Python-specific, False for other langs
                    "handlers": [{"type": str|None, "line": int}]
                }
            ]
        """
        pass

    @abstractmethod
    def extract_assert_statements(self) -> list:
        """
        Returns:
            [{"line": int, "condition": str, "message": str|None}]
        """
        pass

    @abstractmethod
    def analyze_imports(self) -> list:
        """
        Returns:
            [
                {
                    "module": str,
                    "alias": str|None,
                    "names": list|None,
                    "line": int,
                    "category": str    # "stdlib" | "third_party" | "local"
                }
            ]
        """
        pass

    @abstractmethod
    def detect_async_patterns(self) -> dict:
        """
        Returns:
            {
                "async_functions": int,
                "await_count": int,
                "async_for_count": int,
                "async_with_count": int,
                "is_async_code": bool
            }
        """
        pass

    @abstractmethod
    def detect_entry_points(self) -> list:
        """
        Returns:
            [
                {
                    "type": str,           # "function" | "class" | "main_block"
                    "name": str,
                    "line": int,
                    "public_methods": list|None
                }
            ]
        """
        pass

    @abstractmethod
    def extract_operation_vocabulary(self) -> list:
        """
        Returns:
            [{"category": str, "name": str}]

        Categories: "builtin_or_func", "method", "qualified",
                    "operator", "control"
        """
        pass

    @abstractmethod
    def compute_cyclomatic_complexity(self) -> list:
        """
        Returns:
            [{"function": str, "line": int, "complexity": int}]
        """
        pass

    @abstractmethod
    def build_call_graph(self) -> dict:
        """
        Returns:
            {"func_name": {"callee1", "callee2", ...}}
        """
        pass

    @abstractmethod
    def detect_global_variable_usage(self) -> list:
        """
        Returns:
            [
                {
                    "function": str,
                    "line": int,
                    "declared_global": list[str],
                    "references_module_vars": list[str]
                }
            ]
        """
        pass

    @abstractmethod
    def count_comprehensions(self) -> dict:
        """
        Returns:
            {"list": int, "dict": int, "set": int, "generator": int}
        """
        pass

    def get_executable_lines(self) -> list:
        """
        Default implementation: treat all non-blank, non-comment lines as executable.
        Language-specific parsers can override with more precise logic.
        """
        executable = set()
        for i, line in enumerate(self.source_code.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            executable.add(i)
        return list(executable)