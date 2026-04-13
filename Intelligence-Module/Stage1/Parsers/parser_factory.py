"""
Parser Factory — dispatches to the correct parser based on language.

Single entry point for all downstream consumers.
Usage:
    from Stage1.Parsers.parser_factory import get_parser
    parser = get_parser("python", source_code)
    parser.parse()
    features = parser.extract_structural_summary()
"""

from Stage1.Parsers.python_parser import PythonParser
from Stage1.Parsers.js_ts_parser import JSTSParser
from Stage1.Parsers.java_parser import JavaParser
from Stage1.Parsers.c_cpp_parser import CCppParser


def get_parser(language: str, source_code: str):
    """
    Returns the appropriate parser instance for the given language.

    Args:
        language: one of "python", "javascript", "typescript", "java", "c", "cpp"
        source_code: the raw source code string

    Returns:
        ParserBase subclass instance (already initialized, not yet parsed)

    Raises:
        ValueError: if language is not supported
    """
    if language == "python":
        return PythonParser(source_code)

    elif language in ("javascript", "typescript"):
        return JSTSParser(source_code, language)

    elif language == "java":
        return JavaParser(source_code)

    elif language in ("c", "cpp"):
        return CCppParser(source_code, language)

    else:
        raise ValueError(f"No parser available for language: {language}")