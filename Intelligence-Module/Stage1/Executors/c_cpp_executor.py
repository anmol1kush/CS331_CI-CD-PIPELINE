"""
C/C++ Executor — compiles via gcc/g++, runs binary subprocess.

Coverage: approximate (all executable lines on success).
Future: gcov-based precise coverage.
"""

import subprocess
import tempfile
import os
import json
import time
from Stage1.config import TEST_TIMEOUT
from Stage1.Executors.executor_base import ExecutorBase
from Stage1.Executors.type_marshaller import get_marshalling


class CCppExecutor(ExecutorBase):

    def __init__(self, language="c"):
        self.language = language
        self.compiler = "gcc" if language == "c" else "g++"
        self.suffix = ".c" if language == "c" else ".cpp"

    def execute_callable(self, source_code, tests, structural_features=None):
        """
        C/C++ callable mode: wrap source with a main() that calls the function.
        """
        results = []
        all_executed_lines = set()

        for ind, test in enumerate(tests):
            method_name = test.get("method_name")
            test_input = test.get("input", [])

            wrapper = self.buildcallable_wrapper(
                source_code, method_name, test_input, structural_features
            )
            result = self.compile_and_run(wrapper)
            result["test_id"] = ind

            per_test_lines = result.pop("executed_lines", set())
            all_executed_lines.update(per_test_lines)
            result["per_test_executed_lines"] = per_test_lines
            results.append(result)

        return results, all_executed_lines

    def execute_stdin(self, source_code, tests):
        results = []
        all_executed_lines = set()

        # Compile once, run multiple times
        binary_path = self.compile(source_code)
        if binary_path is None:
            for ind, test in enumerate(tests):
                results.append({
                    "status": "exception",
                    "output": None,
                    "error": "Compilation failed",
                    "runtime": 0,
                    "test_id": ind,
                    "per_test_executed_lines": set(),
                    "called_operations": []
                })
            return results, all_executed_lines

        try:
            for ind, test in enumerate(tests):
                fake_input = test.get("input", "")
                result = self.run_binary(binary_path, stdin_input=fake_input)
                result["test_id"] = ind

                per_test_lines = result.pop("executed_lines", set())
                all_executed_lines.update(per_test_lines)
                result["per_test_executed_lines"] = per_test_lines
                results.append(result)
        finally:
            if os.path.exists(binary_path):
                os.remove(binary_path)

        return results, all_executed_lines

    def execute_script(self, source_code):
        result = self.compile_and_run(source_code)
        result["test_id"] = 0

        per_test_lines = result.pop("executed_lines", set())
        result["per_test_executed_lines"] = per_test_lines

        return [result], per_test_lines

    def buildcallable_wrapper(self, source_code, method_name, test_input, structural_features=None):
        """Build a C/C++ wrapper with main() that calls the target function."""
        marshalling = get_marshalling(
            source_code, structural_features, method_name, test_input, self.language
        )

        if marshalling["needs_marshalling"]:
            helper_code = marshalling["helper_code"]
            arg_exprs = marshalling["arg_expressions"]
            setup_code = marshalling.get("setup_code", "")
            output_ser = marshalling["output_serializer"]
            args_str = ", ".join(arg_exprs)

            if self.language == "c":
                wrapper = f"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

{source_code}

{helper_code}

int main() {{
{setup_code}
    struct ListNode* _result = {method_name}({args_str});
    {output_ser}(_result);
    printf("\\n");
    return 0;
}}
"""
            else:
                wrapper = f"""
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <string>
#include <iostream>
using namespace std;

{source_code}

{helper_code}

int main() {{
{setup_code}
    Solution sol;
    auto _result = sol.{method_name}({args_str});
    cout << {output_ser}(_result) << endl;
    return 0;
}}
"""
            return wrapper

        args_str = ", ".join(self.c_literal(arg) for arg in test_input)

        wrapper = f"""
#include <stdio.h>
#include <stdlib.h>

{source_code}

int main() {{
    printf("%d\\n", {method_name}({args_str}));
    return 0;
}}
"""
        return wrapper

    def c_literal(self, value):
        if isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, float):
            return str(value)
        elif isinstance(value, str):
            return f'"{value}"'
        return str(value)

    def compile(self, code):
        """Compile source to binary. Returns binary path or None on failure."""
        try:
            src_fd, src_path = tempfile.mkstemp(suffix=self.suffix)
            bin_fd, bin_path = tempfile.mkstemp(suffix="")

            os.close(src_fd)
            os.close(bin_fd)

            with open(src_path, 'w', encoding='utf-8') as f:
                f.write(code)

            proc = subprocess.run(
                [self.compiler, src_path, "-o", bin_path, "-lm"],
                capture_output=True, text=True,
                timeout=TEST_TIMEOUT
            )

            os.remove(src_path)

            if proc.returncode != 0:
                if os.path.exists(bin_path):
                    os.remove(bin_path)
                return None

            return bin_path

        except Exception:
            return None

    def run_binary(self, binary_path, stdin_input=None):
        """Run a compiled binary."""
        start = time.time()

        try:
            proc = subprocess.run(
                [binary_path],
                input=stdin_input,
                capture_output=True, text=True,
                timeout=TEST_TIMEOUT
            )

            runtime = time.time() - start

            if proc.returncode != 0:
                return {
                    "status": "crash",
                    "output": None,
                    "error": proc.stderr.strip() or f"Exit code: {proc.returncode}",
                    "runtime": runtime,
                    "executed_lines": set(),
                    "called_operations": []
                }

            stdout = proc.stdout.strip()
            output = stdout
            try:
                output = json.loads(stdout)
            except (json.JSONDecodeError, ValueError):
                pass

            return {
                "status": "success",
                "output": output,
                "error": None,
                "runtime": runtime,
                "executed_lines": self.approximatecoverage(open(binary_path + ".c").read()
                                                              if os.path.exists(binary_path + ".c")
                                                              else ""),
                "called_operations": []
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "output": None,
                "error": f"Execution exceeded {TEST_TIMEOUT} seconds",
                "runtime": time.time() - start,
                "executed_lines": set(),
                "called_operations": []
            }

        except Exception as e:
            return {
                "status": "crash",
                "output": None,
                "error": str(e),
                "runtime": time.time() - start,
                "executed_lines": set(),
                "called_operations": []
            }

    def compile_and_run(self, code, stdin_input=None):
        """Compile and run in one step."""
        start = time.time()
        binary_path = self.compile(code)

        if binary_path is None:
            return {
                "status": "exception",
                "output": None,
                "error": "Compilation failed",
                "runtime": time.time() - start,
                "executed_lines": set(),
                "called_operations": []
            }

        try:
            result = self.run_binary(binary_path, stdin_input=stdin_input)
            # Override coverage with source-based approximation
            result["executed_lines"] = self.approximatecoverage(code)
            return result
        finally:
            if os.path.exists(binary_path):
                os.remove(binary_path)

    def approximatecoverage(self, code):
        if not code:
            return set()
        lines = set()
        in_blockcomment = False
        for i, line in enumerate(code.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if "/*" in stripped:
                in_blockcomment = True
            if in_blockcomment:
                if "*/" in stripped:
                    in_blockcomment = False
                continue
            if stripped.startswith("//"):
                continue
            if stripped.startswith("#"):
                continue
            lines.add(i)
        return lines