import subprocess
from typing import Dict

def run_in_sandbox(code_file: str, timeout: int = 5) -> Dict:
    try:
        proc = subprocess.run(
            ["python", code_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "passed": proc.returncode == 0,
            "log": (proc.stdout or "") + (proc.stderr or "")
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "log": f"Timeout > {timeout}s"}
    except Exception as e:
        return {"passed": False, "log": f"Error: {e}"}