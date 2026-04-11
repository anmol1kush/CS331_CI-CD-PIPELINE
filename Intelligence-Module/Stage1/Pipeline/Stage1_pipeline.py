"""
Stage-1 Pipeline

Orchestrates the entire Stage-1 intelligent testing flow.

Steps:
1. Run semantic analysis
2. Initialize agent state
3. Start environment loop
4. Collect final state
5. Produce structured Stage-1 output
"""

from Stage1.Deterministic.Stage1_Semantic import Semantic_Engine
from Stage1.Core.State import State
from Stage1.Core.Environment import Environment
from Stage1.config import MAX_ITERATIONS
from Stage1.Algo.hybrid_search import Hybrid_Search


def run_stage1(stage0_result: dict, source_code: str, user_context: str = None):
    # Stage-1.1–1.3 : Semantic analysis
    semantic_engine = Semantic_Engine(stage0_result, source_code)
    semantic_output = semantic_engine.run()

    execution_model = semantic_output.get("execution_model")
    structural_features = semantic_output.get("structural_features")

    # Initialize Agent State
    state = State.from_semantic_output(semantic_output, user_context=user_context)

    # Create Environment
    algorithm = Hybrid_Search()
    env = Environment(state, algorithm, max_iterations=MAX_ITERATIONS)

    # Run Agent Loop
    final_state = env.run()

    # Build Stage-1 Output
    stage1_output = {
        "stage": 1,
        "status": "STAGE1_COMPLETE",
        "language": stage0_result.get("language"),
        "execution_model": execution_model,
        "structural_features": structural_features,
        "coverage": {
            "line": final_state.line_coverage,
            "branch": final_state.branch_coverage
        },
        "bugs": {
            "exceptions": final_state.exceptions,
            "failures": final_state.failures,
            "incorrect_outputs": final_state.incorrect_outputs
        },
        "executed_tests": final_state.executed_tests,
        "generated_test_cases": final_state.generated_tests
    }

    return stage1_output