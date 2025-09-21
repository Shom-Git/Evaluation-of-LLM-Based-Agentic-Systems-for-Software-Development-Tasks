from typing import Dict, Any


def run_tests_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes candidate_code with tests inside sandbox.
    Currently a stub returning a fake result.
    """
    candidate_code = state.get("candidate_code", "")
    tests = state.get("tests", "")

    # TODO: Implement pytest execution inside sandbox
    result = {"passed": False, "log": "sandbox not implemented yet"}

    return {**state, "test_result": result}
