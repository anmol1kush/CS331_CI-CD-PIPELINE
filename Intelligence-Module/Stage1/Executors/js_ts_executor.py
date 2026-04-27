"""
JS/TS Executor — runs JavaScript/TypeScript code via Node.js subprocess.

Coverage collection: parses executed line numbers from Node.js
inspector output or c8 coverage tool.

For the current increment, coverage is approximate —
we mark all non-comment, non-blank lines as executed on success.
Full coverage via c8 is a future increment.
"""

import subprocess
import tempfile
import os
import json
import time
from Stage1.config import TEST_TIMEOUT
from Stage1.Executors.executor_base import ExecutorBase
from Stage1.Executors.type_marshaller import get_marshalling


class JSTSExecutor(ExecutorBase):

    def __init__(self, language="javascript"):
        self.language = language
        self.suffix = ".ts" if language == "typescript" else ".js"
        # TS needs transpilation before execution
        self.needs_transpile = language == "typescript"

    def execute_callable(self, source_code, tests, structural_features=None):
        results = []
        all_executed_lines = set()

        for ind, test in enumerate(tests):
            method_name = test.get("method_name")
            test_input = test.get("input", [])

            marshalling = get_marshalling(
                source_code, structural_features, method_name, test_input, self.language
            )

            if marshalling["needs_marshalling"]:
                wrapper = self._build_marshalled_wrapper(
                    source_code, method_name, test_input, marshalling
                )
            else:
                input_json = json.dumps(test_input)
                wrapper = self.build_callable_wrapper(source_code, method_name, input_json)

            result = self.run_node(wrapper)
            result["test_id"] = ind

            per_test_lines = result.pop("executed_lines", set())
            all_executed_lines.update(per_test_lines)
            result["per_test_executed_lines"] = per_test_lines
            results.append(result)

        return results, all_executed_lines

    def execute_stdin(self, source_code, tests):
        results = []
        all_executed_lines = set()

        for ind, test in enumerate(tests):
            fake_input = test.get("input", "")

            result = self.run_node(source_code, stdin_input=fake_input)
            result["test_id"] = ind

            per_test_lines = result.pop("executed_lines", set())
            all_executed_lines.update(per_test_lines)
            result["per_test_executed_lines"] = per_test_lines
            results.append(result)

        return results, all_executed_lines

    def execute_script(self, source_code):
        result = self.run_node(source_code)
        result["test_id"] = 0

        per_test_lines = result.pop("executed_lines", set())
        result["per_test_executed_lines"] = per_test_lines

        return [result], per_test_lines

    def build_callable_wrapper(self, source_code, method_name, input_json):
        """Build a JS wrapper that defines the source, calls the method, prints JSON output."""
        return f"""
// --- Source code ---
{source_code}

// --- Test harness ---
try {{
    const args = {input_json};
    let result;
    if (typeof Solution !== 'undefined') {{
        const instance = new Solution();
        result = instance.{method_name}(...args);
    }} else if (typeof {method_name} === 'function') {{
        result = {method_name}(...args);
    }} else if (typeof module !== 'undefined' && module.exports) {{
        const exported = module.exports;
        if (typeof exported.{method_name} === 'function') {{
            result = exported.{method_name}(...args);
        }} else if (typeof exported === 'function') {{
            result = exported(...args);
        }}
    }}
    console.log(JSON.stringify(result));
}} catch (e) {{
    console.error("__EXCEPTION__:" + e.message);
    process.exit(1);
}}
"""

    def _build_marshalled_wrapper(self, source_code, method_name, test_input, marshalling):
        """Build a JS wrapper with type marshalling for complex types."""
        helper_code = marshalling["helper_code"]
        arg_exprs = marshalling["arg_expressions"]
        output_ser = marshalling["output_serializer"]
        args_call = ", ".join(arg_exprs)

        return f"""
// --- Source code ---
{source_code}

// --- Marshalling helpers ---
{helper_code}

// --- Test harness ---
try {{
    let result;
    if (typeof Solution !== 'undefined') {{
        const instance = new Solution();
        result = instance.{method_name}({args_call});
    }} else if (typeof {method_name} === 'function') {{
        result = {method_name}({args_call});
    }}
    console.log(JSON.stringify({output_ser}(result)));
}} catch (e) {{
    console.error("__EXCEPTION__:" + e.message);
    process.exit(1);
}}
"""

    def run_node(self, code, stdin_input=None):
        """Execute JS code via node subprocess."""
        tmp_path = None
        start = time.time()

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix=self.suffix,
                                             delete=False, encoding='utf-8') as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            # For TypeScript, transpile first
            if self.needs_transpile:
                transpile_result = subprocess.run(
                    ["tsc", "--outDir", os.path.dirname(tmp_path),
                     "--allowJs", "--esModuleInterop", tmp_path],
                    capture_output=True, text=True, timeout=TEST_TIMEOUT
                )
                if transpile_result.returncode != 0:
                    return {
                        "status": "exception",
                        "output": None,
                        "error": f"TypeScript compilation failed: {transpile_result.stderr.strip()}",
                        "runtime": time.time() - start,
                        "executed_lines": set(),
                        "called_operations": []
                    }
                # Run the transpiled .js file
                tmp_path = tmp_path.replace(".ts", ".js")

            proc = subprocess.run(
                ["node", tmp_path],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=TEST_TIMEOUT
            )

            runtime = time.time() - start

            if proc.returncode != 0:
                stderr = proc.stderr.strip()
                if "__EXCEPTION__:" in stderr:
                    error_msg = stderr.split("__EXCEPTION__:")[-1].strip()
                    return {
                        "status": "exception",
                        "output": None,
                        "error": error_msg,
                        "runtime": runtime,
                        "executed_lines": set(),
                        "called_operations": []
                    }
                return {
                    "status": "crash",
                    "output": None,
                    "error": stderr,
                    "runtime": runtime,
                    "executed_lines": set(),
                    "called_operations": []
                }

            stdout = proc.stdout.strip()

            # Try to parse JSON output for callable mode
            output = stdout
            try:
                output = json.loads(stdout)
            except (json.JSONDecodeError, ValueError):
                pass

            # Approximate coverage: all non-blank non-comment lines
            executed_lines = self.approximate_coverage(code)

            return {
                "status": "success",
                "output": output,
                "error": None,
                "runtime": runtime,
                "executed_lines": executed_lines,
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

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            # Clean up .js if TS was transpiled
            js_path = (tmp_path or "").replace(".ts", ".js")
            if js_path != tmp_path and os.path.exists(js_path):
                os.remove(js_path)

    def approximate_coverage(self, code):
        """
        Approximate coverage — marks all executable lines as covered on success.
        Future: replace with c8-based precise coverage.
        """
        lines = set()
        for i, line in enumerate(code.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                continue
            lines.add(i)
        return lines