'''
Stage0: Compilation / Syntax Check (Multi-Error Aware)
'''
import os
import subprocess
import tempfile
import re

TIMEOUT_SEC = 3

# Rule registry for the errors types in the languages(c, cpp, java)
ERROR_RULES = [
    {
        "type": "SyntaxError",
        "patterns": [
            r"\bexpected\b",
            r"syntax error",
            r"illegal start",
            r"invalid syntax"
        ],
        "languages": {"c", "cpp", "java"}
    },
    {
        "type": "NameError",
        "patterns": [
            r"undeclared",
            r"cannot find symbol",
            r"not declared"
        ],
        "languages": {"c", "cpp", "java"}
    },
    {
        "type": "TypeError",
        "patterns": [
            r"incompatible types",
            r"type mismatch"
        ],
        "languages": {"c", "cpp", "java"}
    },
    {
        "type": "ImportError",
        "patterns": [
            r"no such file",
            r"cannot open include",
            r"package .* does not exist"
        ],
        "languages": {"c", "cpp", "java"}
    },
    {
        "type": "FileStructureError",
        "patterns": [
            r"public class .* should be declared in a file named"
        ],
        "languages": {"java"}
    }
]

def file_reader(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        _, ext = os.path.splitext(file_path)
        language = infer_language(ext)

        return compile_test(code, language)

    except Exception as e:
        return {
            "stage": 0,
            "status": "FAIL",
            "check_type": "compile_only",
            "language": None,
            "executed": False,
            "total_errors": 1,
            "errors": [{
                "file": file_path,
                "line": None,
                "column": None,
                "message": str(e),
                "error_type": type(e).__name__
            }]
        }

def infer_language(ext: str):
    if ext == ".py":
        return "python"
    if ext == ".c":
        return "c"
    if ext == ".cpp":
        return "cpp"
    if ext == ".java":
        return "java"
    raise ValueError("Unsupported language")

def classify_from_stderr(message: str, language: str = None) -> str:
    msg = message.lower()

    for rule in ERROR_RULES:
        if language and language not in rule["languages"]:
            continue

        for pattern in rule["patterns"]:
            if re.search(pattern, msg):
                return rule["type"]

    return "CompileError"

def extract_errors_by_language(stderr: str, language: str):
    if language in ("c", "cpp"):
        return extract_gcc_errors(stderr, language)
    elif language == "java":
        return extract_javac_errors(stderr)
    else:
        return []

def extract_gcc_errors(stderr: str, language: str):
    errors = []
    pattern = r"^(.*?):\d+:(?:\d+:)?\s*error:\s*(.*)$"

    for line in stderr.splitlines():
        match = re.match(pattern, line.strip())
        if match:
            message = match.group(2).strip()
            errors.append({
                "error_type": classify_from_stderr(message, language),
                "error": message
            })

    return errors

def extract_javac_errors(stderr: str):
    errors = []
    pattern = r"^(.*?):\d+:\s*error:\s*(.*)$"

    for line in stderr.splitlines():
        match = re.match(pattern, line.strip())
        if match:
            message = match.group(2).strip()
            errors.append({
                "error_type": classify_from_stderr(message, "java"),
                "error": message
            })

    return errors

def standard_pass(language: str):
    return {
        "stage": 0,
        "status": "PASS",
        "check_type": "compile_only",
        "language": language,
        "executed": False,
        "total_errors": 0,
        "errors": []
    }

def standard_fail(language: str, errors: list):
    return {
        "stage": 0,
        "status": "FAIL",
        "check_type": "compile_only",
        "language": language,
        "executed": False,
        "total_errors": len(errors),
        "errors": errors
    }

def compile_test(code: str, language: str):
    try:
        if language == "python":
            try:
                compile(code, "<submitted_code>", "exec")
                return standard_pass(language)
            except SyntaxError as e:
                return standard_fail(language, [{
                    "error_type": "SyntaxError",
                    "error": f"{e.msg} (<submitted_code>, line {e.lineno})"
                }])
        
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=language_extension(language)) as tmp:
                tmp.write(code.encode("utf-8"))
                tmp_path = tmp.name

            try:
                run_compiler(tmp_path, language)
                return standard_pass(language)
            finally:
                os.remove(tmp_path)


    except subprocess.TimeoutExpired:
        return standard_fail(language, [{
            "error_type": "TIMEOUT",
            "error": f"Compilation exceeded {TIMEOUT_SEC} seconds"
        }])


    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip()
        errors = extract_errors_by_language(error_msg, language)

        if not errors:
            errors = [{
                "error_type": "CompileError",
                "error": error_msg
            }]

        return standard_fail(language, errors)

    except Exception as e:
        return standard_fail(language, [{
            "error_type": type(e).__name__,
            "error": str(e)
        }])

def run_compiler(file_path: str, language: str):
    if language == "c":
        subprocess.run(
            ["gcc", "-fsyntax-only", file_path],
            check=True,
            capture_output=True,
            text=True,
            timeout = TIMEOUT_SEC
        )
    elif language == "cpp":
        subprocess.run(
            ["g++", "-fsyntax-only", file_path],
            check=True,
            capture_output=True,
            text=True,
            timeout = TIMEOUT_SEC
        )
    elif language == "java":
        subprocess.run(
            ["javac", file_path],
            check=True,
            capture_output=True,
            text=True,
            timeout = TIMEOUT_SEC
        )

def language_extension(language: str):
    return {
        "c": ".c",
        "cpp": ".cpp",
        "java": ".java"
    }[language]

# result_py = file_reader("Sample code 1.py")
# print(result_py)
#
# result_c = file_reader("Sample code 1.c")
# print(result_c)
#
# result_cpp = file_reader("Sample code 1.cpp")
# print(result_cpp)
#
# result_java = file_reader("Sample Code 1.java")
# print(result_java)
#
# res_test_code = file_reader("Test Code 1.py")
# print(res_test_code)

# base_dir = os.path.dirname(os.path.abspath(__file__))
#
# test_file = os.path.join(base_dir, "Sample Code 1.py")
# res_test_code = file_reader(test_file)
# print(res_test_code)
