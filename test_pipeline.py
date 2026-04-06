import os
import sys

# Add the Intelligence-Module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Intelligence-Module'))

from Orchestrator import Pipeline_Orchestrator

def test_pipeline_directly():
    # Test file path
    test_file = os.path.join(os.path.dirname(__file__), 'uploads', 'test_sample.py')

    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return

    print(f"Testing pipeline with file: {test_file}")

    try:
        # Change to Intelligence-Module directory
        original_cwd = os.getcwd()
        intelligence_dir = os.path.join(os.path.dirname(__file__), 'Intelligence-Module')
        os.chdir(intelligence_dir)

        print("Running pipeline...")
        pipeline = Pipeline_Orchestrator(test_file)
        result = pipeline.run_pipeline()

        print(f"Pipeline result: {result}")

        # Check if JSON results were generated
        json_results_path = os.path.join(intelligence_dir, 'Stage1', 'Tests', 'Test_Cases.json')
        if os.path.exists(json_results_path):
            print(f"JSON results generated at: {json_results_path}")
            with open(json_results_path, 'r') as f:
                content = f.read()
                print("JSON content (first 500 chars):")
                print(content[:500])
        else:
            print("No JSON results found")

        # Change back
        os.chdir(original_cwd)

    except Exception as e:
        print(f"Error running pipeline: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline_directly()