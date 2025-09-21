from typing import Dict

def decision_node(state: Dict) -> Dict:
    test_result = state.get("test_result", {})
    done = test_result.get("passed", False)
    return {**state, "done": done}