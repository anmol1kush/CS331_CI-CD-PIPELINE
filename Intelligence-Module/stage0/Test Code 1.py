import pytest
from your_stage0_module import file_reader


# --------------------------
# 1️⃣ SCHEMA VALIDATION
# --------------------------

def validate_schema(result):
    required_global = {
        "stage", "status", "check_type",
        "language", "executed",
        "total_errors", "errors"
    }

    assert set(result.keys()) == required_global

    assert isinstance(result["stage"], int)
    assert result["status"] in ["PASS", "FAIL"]
    assert result["check_type"] == "compile_only"
    assert isinstance(result["language"], str)
    assert isinstance(result["executed"], bool)
    assert isinstance(result["total_errors"], int)
    assert isinstance(result["errors"], list)

    for err in result["errors"]:
        assert set(err.keys()) == {"error_type", "error"}
        assert isinstance(err["error_type"], str)
        assert isinstance(err["error"], str)


# --------------------------
# 2️⃣ PASS TESTS
# --------------------------

def test_python_pass():
    result = file_reader("valid.py")
    validate_schema(result)
    assert result["status"] == "PASS"
    assert result["total_errors"] == 0


def test_c_pass():
    result = file_reader("valid.c")
    validate_schema(result)
    assert result["status"] == "PASS"
    assert result["total_errors"] == 0


def test_cpp_pass():
    result = file_reader("valid.cpp")
    validate_schema(result)
    assert result["status"] == "PASS"


def test_java_pass():
    result = file_reader("Valid.java")
    validate_schema(result)
    assert result["status"] == "PASS"


# --------------------------
# 3️⃣ MULTIPLE ERROR TESTS
# --------------------------

def test_c_multiple_errors():
    result = file_reader("test_multi.c")
    validate_schema(result)
    assert result["status"] == "FAIL"
    assert result["total_errors"] >= 2


def test_cpp_multiple_errors():
    result = file_reader("test_multi.cpp")
    validate_schema(result)
    assert result["status"] == "FAIL"
    assert result["total_errors"] >= 2


def test_java_multiple_errors():
    result = file_reader("TestMulti.java")
    validate_schema(result)
    assert result["status"] == "FAIL"
    assert result["total_errors"] >= 2


# --------------------------
# 4️⃣ ERROR TYPE VALIDATION
# --------------------------

def test_error_types_are_valid():
    result = file_reader("test_multi.c")
    validate_schema(result)

    allowed_types = {
        "SyntaxError",
        "NameError",
        "TypeError",
        "ImportError",
        "FileStructureError",
        "CompileError",
        "TIMEOUT"
    }

    for err in result["errors"]:
        assert err["error_type"] in allowed_types


# --------------------------
# 5️⃣ TIMEOUT TEST
# --------------------------

def test_timeout(monkeypatch):

    import subprocess

    def mock_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="gcc", timeout=3)

    monkeypatch.setattr("subprocess.run", mock_run)

    result = file_reader("valid.c")
    validate_schema(result)

    assert result["status"] == "FAIL"
    assert result["errors"][0]["error_type"] == "TIMEOUT"


# --------------------------
# 6️⃣ UNSUPPORTED LANGUAGE
# --------------------------

def test_unsupported_extension():
    with pytest.raises(ValueError):
        file_reader("file.go")
