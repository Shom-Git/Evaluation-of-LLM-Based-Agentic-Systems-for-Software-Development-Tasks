from typing import Dict
from nodes.sandbox_runner import run_in_sandbox
import os

SANDBOX_DIR = "/home/coder/project/experiments/sandbox_outputs"

def run_tests_node(state: Dict) -> Dict:
    os.makedirs(SANDBOX_DIR, exist_ok=True)
    candidate_file = os.path.join(SANDBOX_DIR, "candidate_temp.py")

    with open(candidate_file, "w") as f:
        f.write(state["candidate_code"] + "\n" + state.get("tests", ""))

    result = run_in_sandbox(candidate_file)
    return {**state, "test_result": result, "candidate_file": candidate_file}

