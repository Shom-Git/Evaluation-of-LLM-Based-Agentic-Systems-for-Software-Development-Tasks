import argparse
import json
import datetime
from langgraph_workflows.fix_agent import run_fix_agent_for_example
from evaluate import evaluate_dataset


def load_dataset_task(data_path: str, task_id: str):
    """Load a specific task from HumanEvalFix dataset."""
    with open(data_path, 'r') as f:
        for line in f:
            if line.strip():
                task = json.loads(line)
                if task['task_id'] == task_id:
                    return task
    raise ValueError(f"Task {task_id} not found in dataset")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="LLM-based Python code fixing agent")
    p.add_argument("--mode", choices=["single", "batch"], default="single")
    p.add_argument("--data", default="data/humanevalpack_python.jsonl", help="JSONL file path")
    p.add_argument("--task-id", help="Specific task ID for single mode (e.g., 'Python/0')")
    p.add_argument("--exp-num", type=int, default=1, help="Experiment number for today")
    a = p.parse_args()

    if a.mode == "single":
        today = datetime.datetime.now()
        day_str = today.strftime("%d")
        exp_name = f"demo_{day_str}_{a.exp_num}"
        
        if a.task_id:
            # Load specific task from dataset
            task = load_dataset_task(a.data, a.task_id)
            buggy = task['buggy_solution']
            tests = task['test']
            task_prompt = task.get('prompt', task.get('docstring', ''))  # Use prompt field, fallback to docstring
            exp_name = f"{a.task_id.replace('/', '_')}_{day_str}_{a.exp_num}"
            print(f"Running task: {a.task_id}")
            print(f"Bug type: {task.get('bug_type', 'unknown')}")
            print(f"Description: {task.get('docstring', 'No description')}")
        else:
            # Default simple example
            buggy = "def mul(a,b): return a+b"
            tests = "assert mul(2,3)==6"
            task_prompt = "Fix the multiplication function that incorrectly uses addition."
        
        st = run_fix_agent_for_example(buggy, tests, exp_name, task_prompt)
        print("Final status:", st["final_status"])
        print("Task directory:", st["task_dir"])
        print("\n=== DEBUGGING ATTEMPTS AND REASONING ===")
        for h in st["history"]:
            print(f"\n--- Attempt {h['attempt']} - {'PASSED' if h['passed'] else 'FAILED'} ---")
            if h.get('reasoning'):
                print("LLM Reasoning:")
                print(h['reasoning'])
            print("\nCandidate Code:")
            print(h.get('candidate_code', 'No code'))
            if not h['passed']:
                print("\nError Log:")
                print(h['log'])
            print("-" * 50)
        
        # Print pass@1 and pass@k metrics
        attempts = st["history"]
        pass_at_1 = 1 if attempts and attempts[0]["passed"] else 0
        pass_at_k = 1 if any(a["passed"] for a in attempts) else 0
        print(f"\n=== METRICS ===")
        print(f"pass@1: {pass_at_1}")
        print(f"pass@k: {pass_at_k}")
        print(f"Total attempts: {len(attempts)}")
    else:
        # Batch mode - evaluate on dataset  
        subset_size = input("Enter subset size for testing (or press Enter for full dataset): ").strip()
        subset_size = int(subset_size) if subset_size else None
        
        print(f"Starting batch evaluation on {a.data}")
        if subset_size:
            print(f"Evaluating subset of {subset_size} problems")
        else:
            print("Evaluating full dataset")
            
        summary = evaluate_dataset(a.data, "experiments/results.json", subset_size)
        print(f"\nEvaluation complete! Results saved to experiments/results.json")
