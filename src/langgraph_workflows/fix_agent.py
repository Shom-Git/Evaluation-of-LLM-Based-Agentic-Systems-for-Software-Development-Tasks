# main workflow (building graph)

import os, time
from typing import Dict
from nodes.llm_node import llm_node
from nodes.sandbox_runner import run_in_sandbox

BASE_DIR = "/home/coder/project/experiments"
MAX_STEPS = 3

def _make_task_dir(task_id: str):
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(BASE_DIR, f"{task_id}_{ts}")
    os.makedirs(path, exist_ok=True)
    return path

def run_fix_agent_for_example(buggy: str, tests: str, task_id="task") -> Dict:
    task_dir = _make_task_dir(task_id)
    state = {"buggy_code": buggy, "tests": tests, "history": []}

    for attempt in range(MAX_STEPS):
        # Pass full history (including error logs) to llm_node for ReAct-style reasoning
        state = llm_node(state)
        candidate = state["candidate_code"]

        # Run candidate in sandbox
        result = run_in_sandbox(candidate, tests, attempt, task_dir)

        # Log attempt
        state["history"].append({
            "attempt": attempt,
            "passed": result["passed"],
            "log": result["log"][:1000],
            "candidate_code": candidate
        })

        # Save log to file
        log_file = os.path.join(task_dir, f"cand_{attempt}.log")
        with open(log_file, "w") as f:
            f.write(result["log"])

        # Save candidate file (already сделано в run_in_sandbox)
        if result["passed"]:
            state.update(final_status="solved", final_file=result["candidate_file"], task_dir=task_dir)
            return state

    state.update(final_status="unsolved", task_dir=task_dir)
    return state
