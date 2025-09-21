import json, time, argparse
from pathlib import Path
from langgraph_workflows.fix_agent import run_fix_agent_for_example

def load_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]

def evaluate_dataset(data_path, out_path):
    data = load_jsonl(data_path)
    results = []
    solved_first = 0

    for i, ex in enumerate(data):
        pid = ex.get("problem_id", f"p{i}")
        print("Running", pid)
        t0 = time.time()
        state = run_fix_agent_for_example(ex["buggy_code"], ex["tests"], task_id=pid)
        dur = time.time() - t0

        first_ok = state["history"][0]["passed"]
        if first_ok:
            solved_first += 1

        results.append({
            "id": pid,
            "status": state["final_status"],
            "attempts": len(state["history"]),
            "first_passed": first_ok,
            "task_dir": state["task_dir"],
            "time_sec": dur
        })

        with open(out_path, "w") as f:
            json.dump({"results": results, "pass@1": solved_first/(i+1)}, f, indent=2)

    print("Final pass@1 =", solved_first/len(data))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--out", default="experiments/results.json")
    a = p.parse_args()
    evaluate_dataset(a.data, a.out)
