from typing import Dict, List, Literal

def should_continue_attempts(state: Dict) -> bool:
    """Determine if we should make another attempt."""
    current_attempt = state.get('current_attempt', 0)
    max_attempts = state.get('max_attempts', 3)
    test_result = state.get('test_result', {})
    
    # Stop if we've reached max attempts
    if current_attempt >= max_attempts:
        return False
    
    # Stop if current attempt passed
    if test_result.get('passed', False):
        return False
    
    # Continue if we have more strategies to try
    return True

def decision_node(state: Dict) -> Dict:
    """
    Decision node that determines workflow direction and next actions.
    """
    test_result = state.get("test_result", {})
    current_attempt = state.get('current_attempt', 0)
    max_attempts = state.get('max_attempts', 3)
    
    # Check if test passed
    if test_result.get("passed", False):
        return {**state, "done": True, "next_step": "end", "final_status": "solved"}
    
    # Check if we should continue
    if current_attempt < max_attempts - 1:
        return {**state, "done": False, "next_step": "retry", "current_attempt": current_attempt + 1}
    else:
        return {**state, "done": True, "next_step": "end", "final_status": "unsolved"}