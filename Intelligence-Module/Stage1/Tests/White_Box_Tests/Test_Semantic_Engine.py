"""
White box test: Semantic Engine
Tests AST parsing, structural feature extraction, recursion detection
"""
from Stage1.Deterministic.Stage1_Semantic import Semantic_Engine

if __name__ == '__main__':
    stage0_pass = {"status": "PASS", "language": "python"}

    # ===== __init__ validation =====
    print("=== Init Validation ===")

    try:
        engine = Semantic_Engine({"status": "FAIL", "language": "python"}, "x=1")
        print("  FAIL status accepted: FAILED")
    except ValueError:
        print("  FAIL status rejected: PASSED")

    try:
        engine = Semantic_Engine(stage0_pass, "x=1")
        print("  PASS status accepted: PASSED")
    except ValueError:
        print("  PASS status accepted: FAILED")

    # ===== initialize — execution model detection =====
    print("\n=== Execution Model Detection ===")

    code = "class Solution:\n    def solve(self): pass"
    engine = Semantic_Engine(stage0_pass, code)
    result = engine.initialize()
    print(f"  class Solution → {result['execution_model']}")

    code = "n = int(input())\nprint(n)"
    engine = Semantic_Engine(stage0_pass, code)
    result = engine.initialize()
    print(f"  input() code → {result['execution_model']}")

    code = "x = 1\ny = 2\nz = x + y"
    engine = Semantic_Engine(stage0_pass, code)
    result = engine.initialize()
    print(f"  plain script → {result['execution_model']}")

    # ===== parse_ast =====
    print("\n=== AST Parsing ===")

    code = "def foo(): return 1"
    engine = Semantic_Engine(stage0_pass, code)
    engine.initialize()
    result = engine.parse_ast()
    print(f"  Valid code ast_status: {result['ast_status']}")

    stage0_c = {"status": "PASS", "language": "c"}
    engine = Semantic_Engine(stage0_c, "int main() {}")
    engine.initialize()
    result = engine.parse_ast()
    print(f"  C language ast_status: {result['ast_status']}")

    # ===== structural features =====
    print("\n=== Structural Features ===")

    code = "def a(): pass\ndef b(): pass\ndef c(): pass"
    engine = Semantic_Engine(stage0_pass, code)
    engine.initialize()
    engine.parse_ast()
    result = engine.extract_structural_features()
    features = result['structural_features']
    print(f"  3 functions → function_count: {features['function_count']}")

    code = "class A: pass\nclass B: pass"
    engine = Semantic_Engine(stage0_pass, code)
    engine.initialize()
    engine.parse_ast()
    result = engine.extract_structural_features()
    features = result['structural_features']
    print(f"  2 classes → class_count: {features['class_count']}")

    code = "for i in range(10):\n    while True:\n        break"
    engine = Semantic_Engine(stage0_pass, code)
    engine.initialize()
    engine.parse_ast()
    result = engine.extract_structural_features()
    features = result['structural_features']
    print(f"  for+while → loop_count: {features['loop_count']}")

    code = "x=1\nif x>0:\n    pass\nif x<0:\n    pass\nif x==0:\n    pass"
    engine = Semantic_Engine(stage0_pass, code)
    engine.initialize()
    engine.parse_ast()
    result = engine.extract_structural_features()
    features = result['structural_features']
    print(f"  3 ifs → branching_factor: {features['branching_factor']}")

    code = "a=1\nb=2\nc=3\nd=4\ne=5"
    engine = Semantic_Engine(stage0_pass, code)
    engine.initialize()
    engine.parse_ast()
    result = engine.extract_structural_features()
    features = result['structural_features']
    print(f"  5 lines → line_count: {features['line_count']}")

    code = "if True:\n    if True:\n        if True:\n            pass"
    engine = Semantic_Engine(stage0_pass, code)
    engine.initialize()
    engine.parse_ast()
    result = engine.extract_structural_features()
    features = result['structural_features']
    print(f"  3 nested ifs → max_nesting_depth: {features['max_nesting_depth']}")

    # ===== recursion detection =====
    print("\n=== Recursion Detection ===")

    code = "def factorial(n):\n    if n<=1: return 1\n    return n * factorial(n-1)"
    engine = Semantic_Engine(stage0_pass, code)
    engine.initialize()
    engine.parse_ast()
    result = engine.extract_structural_features()
    features = result['structural_features']
    print(f"  Direct recursion → detected: {features['direct_recursion']}")

    code = "def a():\n    b()\ndef b():\n    a()"
    engine = Semantic_Engine(stage0_pass, code)
    engine.initialize()
    engine.parse_ast()
    result = engine.extract_structural_features()
    features = result['structural_features']
    print(f"  Mutual recursion → detected: {features['mutual_recursion']}")

    code = "def a():\n    return 1\ndef b():\n    return 2"
    engine = Semantic_Engine(stage0_pass, code)
    engine.initialize()
    engine.parse_ast()
    result = engine.extract_structural_features()
    features = result['structural_features']
    print(f"  No recursion → detected: {features['recursion_detected']}")

    # ===== empty and edge cases =====
    print("\n=== Edge Cases ===")

    engine = Semantic_Engine(stage0_pass, "")
    engine.initialize()
    engine.parse_ast()
    result = engine.extract_structural_features()
    print(f"  Empty code → feature_status: {result['feature_status']}")

    engine = Semantic_Engine(stage0_pass, "# just a comment")
    engine.initialize()
    engine.parse_ast()
    result = engine.extract_structural_features()
    features = result['structural_features']
    print(f"  Comment only → function_count: {features['function_count']}")

    # ===== full run output contract =====
    print("\n=== Full Run Output Contract ===")

    code = "class Solution:\n    def solve(self, n):\n        for i in range(n):\n            if i > 5:\n                return i\n        return -1"
    engine = Semantic_Engine(stage0_pass, code)
    result = engine.run()

    required_keys = ["stage", "status", "language", "execution_model", "ast_status", "feature_status", "structural_features", "normalized_code"]
    for key in required_keys:
        present = key in result
        print(f"  Key '{key}' present: {present}")