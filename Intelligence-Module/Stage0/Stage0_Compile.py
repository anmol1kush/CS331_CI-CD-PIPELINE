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
    },
    {
        "type": "SyntaxError",
        "patterns": [
            r"unexpected token",
            r"unexpected identifier",
            r"unexpected end of input",
            r"unterminated string literal",
            r"missing \) after argument list"
        ],
        "languages": {"javascript", "typescript"}
    },
    {
        "type": "TypeError",
        "patterns": [
            r"type '.*' is not assignable to type",
            r"property '.*' does not exist on type",
            r"cannot find name"
        ],
        "languages": {"typescript"}
    },
    {
        "type": "ImportError",
        "patterns": [
            r"cannot find module",
            r"module not found"
        ],
        "languages": {"javascript", "typescript"}
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
    if ext == ".js":
        return "javascript"
    if ext == ".jsx":
        return "javascript"
    if ext in (".ts", ".tsx"):
        return "typescript"
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
    elif language == "javascript":
        return extract_node_errors(stderr)
    elif language == "typescript":
        return extract_tsc_errors(stderr)
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

def extract_node_errors(stderr: str):
    """Extract errors from Node.js --check output (V8 error format)."""
    errors = []
    # V8 format: file:line — SyntaxError: message
    pattern = r"^.*?:(\d+)\s*\n(.*?Error:\s*.*)$"
    matches = re.findall(pattern, stderr, re.MULTILINE)

    if matches:
        for line_no, message in matches:
            errors.append({
                "error_type": classify_from_stderr(message, "javascript"),
                "error": message.strip()
            })
    else:
        # Fallback: capture any SyntaxError line
        for line in stderr.splitlines():
            if "SyntaxError" in line or "Error" in line:
                errors.append({
                    "error_type": classify_from_stderr(line, "javascript"),
                    "error": line.strip()
                })
                break

    return errors


def extract_tsc_errors(stderr: str):
    """Extract errors from tsc --noEmit output."""
    errors = []
    # tsc format: file(line,col): error TSxxxx: message
    pattern = r"^.*?\(\d+,\d+\):\s*error\s+TS\d+:\s*(.*)$"

    for line in stderr.splitlines():
        match = re.match(pattern, line.strip())
        if match:
            message = match.group(1).strip()
            errors.append({
                "error_type": classify_from_stderr(message, "typescript"),
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

        elif language == "javascript":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".js") as tmp:
                tmp.write(code.encode("utf-8"))
                tmp_path = tmp.name
            try:
                run_compiler(tmp_path, language)
                return standard_pass(language)
            finally:
                os.remove(tmp_path)

        elif language == "typescript":
            # For .tsx/.jsx-style code, determine suffix from context
            suffix = ".ts"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(code.encode("utf-8"))
                tmp_path = tmp.name
            try:
                run_compiler(tmp_path, language)
                return standard_pass(language)
            finally:
                os.remove(tmp_path)
        
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

    elif language == "javascript":
        subprocess.run(
            ["node", "--check", file_path],
            check=True,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SEC
        )

    elif language == "typescript":
        subprocess.run(
            ["tsc", "--noEmit", "--allowJs", "--esModuleInterop", file_path],
            check=True,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SEC
        )

def language_extension(language: str):
    return {
        "c": ".c",
        "cpp": ".cpp",
        "java": ".java",
        "javascript": ".js",
        "typescript": ".ts"
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
# res_test_code = file_reader("Tests Code 1.py")
# print(res_test_code)

# base_dir = os.path.dirname(os.path.abspath(__file__))
#
# test_file = os.path.join(base_dir, "Sample Code 1.py")
# res_test_code = file_reader(test_file)
# print(res_test_code)
