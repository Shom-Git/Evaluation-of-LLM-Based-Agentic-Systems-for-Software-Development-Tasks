import json, time, argparse, os
from pathlib import Path
from langgraph_workflows.fix_agent import run_fix_agent_for_example

def load_jsonl(path):
    """Load HumanEvalFix dataset from JSONL file."""
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]

def evaluate_dataset(data_path, out_path, subset_size=None):
    """
    Evaluate the agent on HumanEvalFix dataset.
    
    Args:
        data_path: Path to JSONL dataset file
        out_path: Path to save results
        subset_size: Optional limit on number of problems to evaluate
    """
    data = load_jsonl(data_path)
    
    if subset_size:
        data = data[:subset_size]
        print(f"Evaluating on subset of {subset_size} problems")
    
    results = []
    solved_first = 0  # pass@1 metric
    solved_any = 0    # pass@k metric (solved in any attempt)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    start_time = time.time()
    
    for i, ex in enumerate(data):
        task_id = ex.get("task_id", f"problem_{i}")
        print(f"\n=== Running {task_id} ({i+1}/{len(data)}) ===")
        
        t0 = time.time()
        
        # Run the agent
        state = run_fix_agent_for_example(
            ex["buggy_solution"], 
            ex["test"], 
            task_id=task_id.replace("/", "_"),
            task_prompt=ex.get("prompt", ex.get("docstring", ""))
        )
        
        dur = time.time() - t0
        
        # Calculate metrics
        first_attempt = state["history"][0] if state["history"] else {"passed": False}
        first_passed = first_attempt["passed"]
        any_passed = state["final_status"] == "solved"
        
        if first_passed:
            solved_first += 1
        if any_passed:
            solved_any += 1
            
        # Store detailed results
        result = {
            "task_id": task_id,
            "bug_type": ex.get("bug_type", "unknown"),
            "final_status": state["final_status"],
            "attempts": len(state["history"]),
            "first_passed": first_passed,
            "any_passed": any_passed,
            "task_dir": state["task_dir"],
            "time_sec": round(dur, 2),
            "reasoning_trace": [h.get("reasoning", "") for h in state["history"]]
        }
        
        results.append(result)
        
        # Calculate running metrics
        current_pass_at_1 = solved_first / (i + 1)
        current_pass_at_k = solved_any / (i + 1)
        
        print(f"Result: {state['final_status']} (first: {first_passed}, any: {any_passed})")
        print(f"Running pass@1: {current_pass_at_1:.3f}, pass@k: {current_pass_at_k:.3f}")
        
        # Save intermediate results
        summary = {
            "dataset": data_path,
            "subset_size": len(data),
            "completed": i + 1,
            "total_time_sec": round(time.time() - start_time, 2),
            "pass_at_1": current_pass_at_1,
            "pass_at_k": current_pass_at_k,
            "results": results
        }
        
        with open(out_path, "w") as f:
            json.dump(summary, f, indent=2)
    
    # Final summary
    final_pass_at_1 = solved_first / len(data)
    final_pass_at_k = solved_any / len(data)
    total_time = time.time() - start_time
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Dataset: {data_path}")
    print(f"Problems evaluated: {len(data)}")
    print(f"Pass@1 (first attempt): {final_pass_at_1:.3f} ({solved_first}/{len(data)})")
    print(f"Pass@k (any attempt): {final_pass_at_k:.3f} ({solved_any}/{len(data)})")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average time per problem: {total_time/len(data):.1f}s")
    
    return summary

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Evaluate LLM agent on HumanEvalFix dataset")
    p.add_argument("--data", default="data/humanevalpack_python.jsonl", help="Path to JSONL dataset")
    p.add_argument("--out", default="experiments/results.json", help="Path to save results")
    p.add_argument("--subset", type=int, help="Evaluate only first N problems for testing")
    a = p.parse_args()
    
    summary = evaluate_dataset(a.data, a.out, a.subset)
    print(f"\nResults saved to: {a.out}")