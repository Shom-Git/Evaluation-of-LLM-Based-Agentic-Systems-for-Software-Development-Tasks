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
        state = llm_node(state)
        candidate = state["candidate_code"]

        # Save candidate + tests
        py_file = os.path.join(task_dir, f"cand_{attempt}.py")
        with open(py_file, "w") as f:
            f.write(candidate + "\n\n" + tests)

        # Run
        result = run_in_sandbox(py_file, timeout=8)

        # Log result
        state["history"].append({
            "attempt": attempt,
            "passed": result["passed"],
            "log": result["log"][:1000]
        })
        with open(os.path.join(task_dir, f"cand_{attempt}.log"), "w") as f:
            f.write(result["log"])

        if result["passed"]:
            state.update(final_status="solved", final_file=py_file, task_dir=task_dir)
            return state

    state.update(final_status="unsolved", task_dir=task_dir)
    return state
