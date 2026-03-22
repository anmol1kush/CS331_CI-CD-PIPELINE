"""
Isolated coverage test — with multiprocessing (matches real pipeline)
"""
from Stage1.Tools.test_executor import run_tests
from Stage1.Tools.coverage_analyzer import compute_coverage

source_code = """
class Solution:
    def twoSum(self, nums, target):
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return []
"""

tests = [
    {
        "strategy": "manual",
        "method_name": "twoSum",
        "input": [[2, 7, 11, 15], 9],
        "expected_output": [0, 1],
        "comparison_mode": "exact"
    },
    {
        "strategy": "manual",
        "method_name": "twoSum",
        "input": [[3, 3], 6],
        "expected_output": [0, 1],
        "comparison_mode": "exact"
    },
    {
        "strategy": "manual",
        "method_name": "twoSum",
        "input": [[1, 2, 3], 99],
        "expected_output": [],
        "comparison_mode": "exact"
    }
]

if __name__ == '__main__':
    print("Running test_executor (with multiprocessing)...")
    results, executed_lines = run_tests(source_code, tests, "callable_method")

    print(f"\nTest results:")
    for r in results:
        print(f"  Test {r['test_id']}: status={r['status']}, output={r.get('output')}")

    print(f"\nExecuted lines: {sorted(executed_lines)}")
    print(f"Number of lines traced: {len(executed_lines)}")

    print("\nRunning coverage_analyzer...")
    coverage = compute_coverage(source_code, executed_lines)

    print(f"Line coverage: {coverage['line_coverage']:.2f}")
    print(f"Branch coverage: {coverage['branch_coverage']:.2f}")