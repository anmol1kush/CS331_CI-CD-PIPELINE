'''
Stage 0: Compilation / Syntax Check
'''
import os
import subprocess
import tempfile
import re

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
            "error_type": type(e).__name__,
            "error": str(e)
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

def classify_from_stderr(stderr: str, language: str = None) -> str:
    msg = stderr.lower()

    for rule in ERROR_RULES:
        if language and language not in rule["languages"]:
            continue

        for pattern in rule["patterns"]:
            if re.search(pattern, msg):
                return rule["type"]

    return "CompileError"

def compile_test(code: str, language: str):
    try:
        if language == "python":
            compile(code, "<submitted_code>", "exec")

        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=language_extension(language)) as tmp:
                tmp.write(code.encode("utf-8"))
                tmp_path = tmp.name

            run_compiler(tmp_path, language)

        return {
            "stage": 0,
            "status": "PASS",
            "check_type": "compile_only",
            "language": language,
            "executed": False,
            "error": None
        }

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip()
        error_type = classify_from_stderr(error_msg)
        return {
            "stage": 0,
            "status": "FAIL",
            "check_type": "compile_only",
            "language": language,
            "executed": False,
            "error_type": error_type,
            "error": error_msg
        }

    except Exception as e:
        return {
            "stage": 0,
            "status": "FAIL",
            "check_type": "compile_only",
            "language": language,
            "executed": False,
            "error_type": type(e).__name__,
            "error": str(e)
        }

def run_compiler(file_path: str, language: str):
    if language == "c":
        subprocess.run(
            ["gcc", "-fsyntax-only", file_path],
            check=True,
            capture_output=True,
            text=True
        )
    elif language == "cpp":
        subprocess.run(
            ["g++", "-fsyntax-only", file_path],
            check=True,
            capture_output=True,
            text=True
        )
    elif language == "java":
        subprocess.run(
            ["javac", "-fsyntax-only", file_path],
            check=True,
            capture_output=True,
            text=True
        )

def language_extension(language: str):
    return {
        "c": ".c",
        "cpp": ".cpp",
        "java": ".java"
    }[language]

result_py = file_reader("Sample code 1.py")
print(result_py)

result_c = file_reader("Sample code 1.c")
print(result_c)

result_cpp = file_reader("Sample code 1.cpp")
print(result_cpp)

result_java = file_reader("Sample Code 1.java")
print(result_java)

