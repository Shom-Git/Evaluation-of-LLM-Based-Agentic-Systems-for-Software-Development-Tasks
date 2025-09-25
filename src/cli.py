import argparse
import json
import datetime
import sys
import os

# Add src to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflows.main_agent import CodeFixingAgent


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
    p.add_argument("--max-attempts", type=int, default=3, help="Maximum number of fix attempts per task")
    p.add_argument("--task-range", help="Task range for batch mode (e.g., '0-9' or '5-15')")
    p.add_argument("--max-tasks", type=int, help="Maximum number of tasks to evaluate in batch mode")
    p.add_argument("--experiments-dir", help="Directory to save experiments (default: ./experiments)")
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
        
        # Create agent and run single task
        base_dir = a.experiments_dir if hasattr(a, 'experiments_dir') and a.experiments_dir else None
        agent = CodeFixingAgent(base_dir=base_dir)
        result = agent.fix_code(
            buggy_code=buggy,
            tests=tests,
            task_id=exp_name,
            task_prompt=task_prompt,
            max_attempts=a.max_attempts
        )
        
        print("Final status:", result["final_status"])
        print("Task directory:", result["task_dir"])
        print("Total attempts:", len(result.get("attempts", [])))
        print("Total time:", f"{result.get('total_time', 0):.2f}s")
        print("LLM calls:", result.get('llm_calls', 0))
        
        # Show attempt details if available
        if result.get("attempts"):
            print("\n=== DEBUGGING ATTEMPTS AND REASONING ===")
            for h in result["attempts"]:
                test_result = h.get('test_result', {})
                print(f"\n--- Attempt {h.get('attempt_num', '?')} - {'PASSED' if test_result.get('passed') else 'FAILED'} ---")
                print(f"Strategy: {h.get('strategy_used', 'unknown')}")
                if h.get('reasoning'):
                    print("Reasoning:")
                    print(h['reasoning'])
                print("\nCandidate Code:")
                print(h.get('candidate_code', 'No code'))
                if not test_result.get('passed'):
                    print("\nError Log:")
                    print(test_result.get('log', 'No error log'))
                print("-" * 50)
            
            # Print pass@1 and pass@k metrics
            attempts = result["attempts"]
            pass_at_1 = 1 if attempts and attempts[0].get('test_result', {}).get('passed') else 0
            pass_at_k = 1 if any(a.get('test_result', {}).get('passed') for a in attempts) else 0
            print(f"\n=== METRICS ===")
            print(f"pass@1: {pass_at_1}")
            print(f"pass@k: {pass_at_k}")
            print(f"Total attempts: {len(attempts)}")
        
        # Additional analysis
        if a.task_id:
            task = load_dataset_task(a.data, a.task_id)
            print(f"\nTask analysis:")
            print(f"  Bug type: {task.get('bug_type', 'unknown')}")
            print(f"  Expected difficulty: {task.get('failure_symptoms', 'unknown')}")
    
    elif a.mode == "batch":
        # Batch mode - evaluate on dataset
        subset_size = a.max_tasks
        task_range = None
        
        # Parse task range if provided
        if a.task_range:
            try:
                start, end = map(int, a.task_range.split('-'))
                task_range = (start, end)
                print(f"Task range: {start} to {end}")
            except ValueError:
                print(f"Invalid task range format: {a.task_range}. Use format like '0-9'")
                sys.exit(1)
        
        # Interactive input if no command line options
        if not subset_size and not task_range:
            choice = input("Choose evaluation mode:\n1. Specify task range (e.g., 0-9)\n2. Specify max tasks\n3. Full dataset\nChoice (1/2/3): ").strip()
            
            if choice == "1":
                range_input = input("Enter task range (e.g., 0-9): ").strip()
                try:
                    start, end = map(int, range_input.split('-'))
                    task_range = (start, end)
                except ValueError:
                    print("Invalid range format")
                    sys.exit(1)
            elif choice == "2":
                subset_input = input("Enter max number of tasks: ").strip()
                subset_size = int(subset_input) if subset_input else None
            # choice == "3" or default: use full dataset
        
        print(f"Starting batch evaluation on {a.data}")
        if task_range:
            print(f"Evaluating tasks {task_range[0]} to {task_range[1]}")
        elif subset_size:
            print(f"Evaluating max {subset_size} tasks")
        else:
            print("Evaluating full dataset")
        
        print(f"Max attempts per task: {a.max_attempts}")
        
        # Create agent and run evaluation
        base_dir = a.experiments_dir if hasattr(a, 'experiments_dir') and a.experiments_dir else None
        agent = CodeFixingAgent(base_dir=base_dir)
        results = agent.evaluate_on_dataset(
            a.data, 
            "experiments/results.json", 
            max_problems=subset_size,
            task_range=task_range,
            max_attempts=a.max_attempts
        )
        
        print(f"\nEvaluation complete! Results saved to experiments/results.json")
        print(f"Pass rate: {results.get('pass_rate', 0):.3f}")
        print(f"Problems solved: {results.get('solved', 0)}/{results.get('total_problems', 0)}")
        print(f"Average attempts: {results.get('avg_attempts', 0):.1f}")
        print(f"Total time: {results.get('total_time', 0):.1f}s")
