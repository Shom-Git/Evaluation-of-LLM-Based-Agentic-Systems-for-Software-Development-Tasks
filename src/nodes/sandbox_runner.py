import subprocess
import os
from typing import Dict

def run_in_sandbox(code: str, tests: str, attempt: int, output_dir: str) -> Dict:
    """
    Run candidate code + tests in a subprocess sandbox.
    Returns dict with pass/fail and error logs.
    """
    os.makedirs(output_dir, exist_ok=True)
    candidate_file = os.path.join(output_dir, f"cand_{attempt}.py")
    with open(candidate_file, "w") as f:
        f.write(code + "\n\n" + tests + "\n")
    try:
        result = subprocess.run(
            ["python", candidate_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        passed = result.returncode == 0
        log = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        passed = False
        log = "Execution timed out"
    # Always pass the full error log to the LLM for better reasoning
    return {"passed": passed, "log": log, "candidate_file": candidate_file}