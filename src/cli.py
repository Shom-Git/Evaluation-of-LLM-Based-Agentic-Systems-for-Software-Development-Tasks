import argparse
from langgraph_workflows.fix_agent import run_fix_agent_for_example
from evaluate import evaluate_dataset

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["single", "batch"], default="single")
    p.add_argument("--data", help="JSONL file for batch mode")
    a = p.parse_args()

    if a.mode == "single":
        buggy = "def mul(a,b): return a+b"
        tests = "assert mul(2,3)==6"
        st = run_fix_agent_for_example(buggy, tests, "demo")
        print("Final:", st["final_status"])
        print("History:", st["history"])
    else:
        if not a.data:
            raise SystemExit("Need --data for batch")
        evaluate_dataset(a.data, "experiments/results.json")
